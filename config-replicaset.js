// rodar somente no primario
var config = {
    '_id': 'mongotor',
    'members': [
        {'_id': 0, 'host': 'localhost:27019', arbiterOnly: true}, // mongo-arbiter
        {'_id': 1, 'host': 'localhost:27017'}, // mongo-01
        {'_id': 2, 'host': 'localhost:27018'} // mongo-02
    ]
};
rs.initiate(config)