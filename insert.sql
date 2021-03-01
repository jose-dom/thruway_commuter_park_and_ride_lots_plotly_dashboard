DROP TABLE IF EXISTS lots;
CREATE TABLE lots (
        lot_name varchar,
        exit varchar,
        operator varchar,
        available_spaces int,
        is_paved varchar,
        light varchar,
        comments varchar,
        latitutide float,
        longtitude float,
        lot_location varchar
    );

\COPY lots FROM 'data/Thruway_Commuter_Park_and_Ride_Lots.csv' DELIMITER ',' CSV HEADER;
