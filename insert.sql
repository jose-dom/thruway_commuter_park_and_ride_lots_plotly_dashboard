DROP TABLE lots;

CREATE TABLE lots (
        id SERIAL,
        title VARCHAR(255),
        exit VARCHAR(255),
        operator VARCHAR(255),
        available_spaces INT,
        is_paved VARCHAR(255),
        light VARCHAR(50),
        comments VARCHAR(255),
        latitutide FLOAT,
        longtitude FLOAT,
        lot_location FLOAT
    )

COPY lots(id, title, exit, operator, available_spaces, is_paved, light, comments, latitutide, longtitude, lot_location)
FROM 'downloaded_lots.csv'
DELIMITER ','
CSV HEADER;