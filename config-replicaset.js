// rodar somente no primario
var config = {
    '_id': 'mongotor',
    'members': [
        {'_id': 0, 'host': 'localhost:27029', arbiterOnly: true}, // mongo-arbiter
        {'_id': 1, 'host': 'localhost:27027', 'priority': 2}, // mongo-01
        {'_id': 2, 'host': 'localhost:27028'} // mongo-02
    ]
};
rs.initiate(config)