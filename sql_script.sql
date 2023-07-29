CREATE DATABASE dbms;
USE dbms;

CREATE TABLE store (
  storeId int NOT NULL,
  storeName varchar(255) NOT NULL,
  storeSlug varchar(255) DEFAULT NULL,
  storeRating decimal(10,2) DEFAULT NULL,
  storeAmtRating int DEFAULT NULL,
  productCount int DEFAULT NULL,
  storeFollowers int DEFAULT NULL,
  storeJoinedDate varchar(255) DEFAULT NULL,
  chatPerformance decimal(10,2) DEFAULT NULL,
  replyRate varchar(255) DEFAULT NULL,
  platformType varchar(255) DEFAULT NULL,
  PRIMARY KEY (storeId)
);

CREATE TABLE product (
  productId int NOT NULL AUTO_INCREMENT,
  productName varchar(255) NOT NULL,
  productSlug text,
  productDesc text,
  sellingPrice decimal(10,2) DEFAULT NULL,
  discountedPrice decimal(10,2) DEFAULT NULL,
  category varchar(255) DEFAULT NULL,
  quantitySold int DEFAULT NULL,
  productLikes int DEFAULT NULL,
  productRatings decimal(10,2) DEFAULT NULL,
  productRatingsAmt int DEFAULT NULL,
  shippingType varchar(255) DEFAULT NULL,
  shipFrom varchar(255) DEFAULT NULL,
  storeId int DEFAULT NULL,
  PRIMARY KEY (productId),
  KEY storeId (storeId),
  CONSTRAINT product_ibfk_1 FOREIGN KEY (storeId) REFERENCES store (storeId)
);

CREATE TABLE account (
  accountId int NOT NULL AUTO_INCREMENT,
  storeId int DEFAULT NULL,
  username varchar(255) NOT NULL,
  email varchar(255) NOT NULL,
  fullName varchar(255) DEFAULT NULL,
  phoneNumber int DEFAULT NULL,
  password varchar(255) DEFAULT NULL,
  hashedPassword varchar(255) NOT NULL,
  address varchar(255) DEFAULT NULL,
  PRIMARY KEY (accountId),
  KEY storeId (storeId),
  CONSTRAINT account_ibfk_1 FOREIGN KEY (storeId) REFERENCES store (storeId)
);

CREATE TABLE watchlist (
  watchlistId int NOT NULL AUTO_INCREMENT,
  storeId int NOT NULL,
  watched_id int NOT NULL,
  watched_type varchar(10) NOT NULL,
  PRIMARY KEY (watchlistId)
);

QUIT
