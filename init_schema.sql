CREATE DATABASE IF NOT EXISTS train_schedule;
USE train_schedule;

CREATE TABLE train_schedule (
    -- id INT AUTO_INCREMENT PRIMARY KEY,
    train_type VARCHAR(10),
    train_code VARCHAR(10),
    breast_feed VARCHAR(5),
    route VARCHAR(10),
    package VARCHAR(5),
    overnight_stn VARCHAR(10),
    line_dir VARCHAR(10),
    line VARCHAR(10),
    dinning VARCHAR(5),
    food_srv VARCHAR(5),
    cripple VARCHAR(5),
    car_class VARCHAR(10),
    bike VARCHAR(5),
    extra_train VARCHAR(5),
    everyday VARCHAR(5),
    note TEXT,
    note_eng TEXT,
    station VARCHAR(10),
    order_in_trip INT,
    dep_time DATETIME,
    arr_time DATETIME,
    route_station VARCHAR(10),
    created_at DATETIME,
    UNIQUE (train_code, station, arr_time)
);
