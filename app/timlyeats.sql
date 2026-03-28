-- ROLE TABLE
CREATE TABLE Role (
    role_id INT PRIMARY KEY AUTO_INCREMENT,
    role_name VARCHAR(50) NOT NULL,
    role_level INT NOT NULL
);

-- USER TABLE
CREATE TABLE User (
    user_id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    phone_number VARCHAR(20),
    role_id INT,
    loyalty_point INT DEFAULT 0,
    FOREIGN KEY (role_id) REFERENCES Role(role_id)
);

-- ITEM TABLE
CREATE TABLE Item (
    item_id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    preparation_time INT,
    price DECIMAL(10,2) NOT NULL
);

-- CART TABLE
CREATE TABLE Cart (
    cart_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    c_date DATETIME,
    u_date DATETIME,
    status VARCHAR(50),
    FOREIGN KEY (user_id) REFERENCES User(user_id)
);

-- CART_ITEM TABLE
CREATE TABLE Cart_Item (
    cart_item_id INT PRIMARY KEY AUTO_INCREMENT,
    cart_id INT NOT NULL,
    item_id INT NOT NULL,
    quantity INT NOT NULL,
    customization_note TEXT,
    FOREIGN KEY (cart_id) REFERENCES Cart(cart_id),
    FOREIGN KEY (item_id) REFERENCES Item(item_id)
);

-- ORDER TABLE
CREATE TABLE Orders (
    order_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    cart_id INT UNIQUE,
    timestamp DATETIME,
    status VARCHAR(50),
    payment_method VARCHAR(50),
    qr_code VARCHAR(255),
    total_amount DECIMAL(10,2),
    FOREIGN KEY (user_id) REFERENCES User(user_id),
    FOREIGN KEY (cart_id) REFERENCES Cart(cart_id)
);

-- ORDER_DETAILS TABLE
CREATE TABLE Order_Details (
    order_item_id INT PRIMARY KEY AUTO_INCREMENT,
    order_id INT NOT NULL,
    item_id INT NOT NULL,
    quantity INT NOT NULL,
    customization_note TEXT,
    FOREIGN KEY (order_id) REFERENCES Orders(order_id),
    FOREIGN KEY (item_id) REFERENCES Item(item_id)
);

-- PAYMENT TABLE
CREATE TABLE Payment (
    payment_id INT PRIMARY KEY AUTO_INCREMENT,
    order_id INT UNIQUE,
    payment_status VARCHAR(50),
    date DATETIME,
    FOREIGN KEY (order_id) REFERENCES Orders(order_id)
);

-- REVIEW TABLE
CREATE TABLE Review (
    review_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    item_id INT NOT NULL,
    rating INT CHECK (rating BETWEEN 1 AND 5),
    comment TEXT,
    FOREIGN KEY (user_id) REFERENCES User(user_id),
    FOREIGN KEY (item_id) REFERENCES Item(item_id)
);


-- adding roles
INSERT INTO role (role_id, role_name, role_level) 
VALUES 
    ('1', 'Customer', '1'),
    ('2', 'Staff', '2'),
    ('3', 'Administrator', '3');