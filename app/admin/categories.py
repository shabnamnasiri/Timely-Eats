import re

import MySQLdb.cursors
from MySQLdb import IntegrityError
from flask import jsonify, redirect, render_template, request, url_for, flash

from app.admin.helpers import admin_required, get_admin_user


SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
DEFAULT_CATEGORIES = [
    ("Starters", "starters"),
    ("Mains", "mains"),
    ("Sides", "sides"),
    ("Desserts", "desserts"),
    ("Drinks", "drinks"),
]


def _ensure_categories_table(mysql):
    cursor = mysql.connection.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS menu_category (
            category_id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            slug VARCHAR(100) NOT NULL UNIQUE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                ON UPDATE CURRENT_TIMESTAMP,
            UNIQUE KEY uniq_menu_category_name (name)
        )
        """
    )

    cursor.executemany(
        """
        INSERT IGNORE INTO menu_category (name, slug)
        VALUES (%s, %s)
        """,
        DEFAULT_CATEGORIES,
    )

    mysql.connection.commit()
    cursor.close()


def _get_categories(mysql):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute(
        """
        SELECT
            c.category_id,
            c.name,
            c.slug,
            COUNT(i.item_id) AS item_count
        FROM menu_category c
        LEFT JOIN item i
            ON LOWER(COALESCE(i.category, '')) = LOWER(c.slug)
        GROUP BY c.category_id, c.name, c.slug
        ORDER BY c.name ASC
        """
    )
    rows = cursor.fetchall()
    cursor.close()
    return rows


def _validate_category_payload(name, slug):
    if not name or not slug:
        return "Category name and slug are required."
    if not SLUG_PATTERN.match(slug):
        return "Slug must use lowercase letters, numbers, and hyphens only."
    return None


def register_admin_category_routes(app, mysql):
    @app.route("/admin/categories", methods=["GET"])
    @app.route("/admin/Categories.html", methods=["GET"])
    @app.route("/Categories.html", methods=["GET"])
    def admin_categories():
        guard = admin_required()
        if guard:
            return guard

        _ensure_categories_table(mysql)
        return render_template(
            "Categories.html",
            categories=_get_categories(mysql),
            user=get_admin_user(mysql),
        )

    @app.route("/admin/categories/list", methods=["GET"])
    def admin_categories_list():
        guard = admin_required()
        if guard:
            return guard

        _ensure_categories_table(mysql)
        return jsonify(_get_categories(mysql))

    @app.route("/admin/categories/create", methods=["POST"])
    def admin_categories_create():
        guard = admin_required()
        if guard:
            return guard

        _ensure_categories_table(mysql)

        name = (request.form.get("name") or "").strip()
        slug = (request.form.get("slug") or "").strip().lower()
        error = _validate_category_payload(name, slug)
        if error:
            flash(error, "danger")
            return redirect(url_for("admin_categories"))

        cursor = mysql.connection.cursor()
        try:
            cursor.execute(
                "INSERT INTO menu_category (name, slug) VALUES (%s, %s)",
                (name, slug),
            )
            mysql.connection.commit()
            flash(f"Category '{name}' created.", "success")
        except IntegrityError:
            flash("Category name or slug already exists.", "warning")
        finally:
            cursor.close()

        return redirect(url_for("admin_categories"))

    @app.route("/admin/categories/update/<int:category_id>", methods=["POST"])
    def admin_categories_update(category_id):
        guard = admin_required()
        if guard:
            return guard

        _ensure_categories_table(mysql)

        name = (request.form.get("name") or "").strip()
        slug = (request.form.get("slug") or "").strip().lower()
        error = _validate_category_payload(name, slug)
        if error:
            flash(error, "danger")
            return redirect(url_for("admin_categories"))

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        try:
            cursor.execute(
                "SELECT slug FROM menu_category WHERE category_id = %s",
                (category_id,),
            )
            existing = cursor.fetchone()
            if not existing:
                flash("Category not found.", "warning")
                return redirect(url_for("admin_categories"))

            old_slug = existing["slug"]
            cursor.execute(
                """
                UPDATE menu_category
                SET name = %s, slug = %s
                WHERE category_id = %s
                """,
                (name, slug, category_id),
            )

            if old_slug != slug:
                cursor.execute(
                    """
                    UPDATE item
                    SET category = %s
                    WHERE LOWER(COALESCE(category, '')) = LOWER(%s)
                    """,
                    (slug, old_slug),
                )

            mysql.connection.commit()
            flash(f"Category '{name}' updated.", "success")

        except IntegrityError:
            flash("Category name or slug already exists.", "warning")
        finally:
            cursor.close()

        return redirect(url_for("admin_categories"))

    @app.route("/admin/categories/delete/<int:category_id>", methods=["POST"])
    def admin_categories_delete(category_id):
        guard = admin_required()
        if guard:
            return guard

        _ensure_categories_table(mysql)

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        try:
            cursor.execute(
                """
                SELECT category_id, name, slug
                FROM menu_category
                WHERE category_id = %s
                """,
                (category_id,),
            )
            row = cursor.fetchone()
            if not row:
                flash("Category not found.", "warning")
                return redirect(url_for("admin_categories"))

            cursor.execute(
                """
                SELECT COUNT(*) AS cnt
                FROM item
                WHERE LOWER(COALESCE(category, '')) = LOWER(%s)
                """,
                (row["slug"],),
            )
            linked_items = cursor.fetchone()["cnt"] or 0
            if linked_items:
                flash(
                    f"Cannot delete '{row['name']}' because it has {linked_items} menu item(s).",
                    "warning",
                )
                return redirect(url_for("admin_categories"))

            cursor.execute(
                "DELETE FROM menu_category WHERE category_id = %s",
                (category_id,),
            )
            mysql.connection.commit()
            flash(f"Category '{row['name']}' deleted.", "success")
        finally:
            cursor.close()

        return redirect(url_for("admin_categories"))
