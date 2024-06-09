from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
import pika

app = Flask(__name__)
# Configuration de la base de données
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://user:password@orders-db:3306/orders'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)



def send_message(order_details):
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
    channel = connection.channel()
    channel.queue_declare(queue='order_queue')
    channel.basic_publish(exchange='', routing_key='order_queue', body=str(order_details))
    connection.close()

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(100), nullable=False)

    def to_json(self):
        return {"id": self.id, "product_id": self.product_id, "quantity": self.quantity, "status": self.status}

@app.route('/orders', methods=['GET'])
def get_orders():
    orders = Order.query.all()
    return jsonify([order.to_json() for order in orders])

@app.route('/orders', methods=['POST'])
def add_order():
    data = request.get_json()
    new_order = Order(product_id=data['product_id'], quantity=data['quantity'], status='pending')
    db.session.add(new_order)
    db.session.commit()
    send_message(new_order.to_json())  # Envoyer les détails de la commande
    return jsonify(new_order.to_json()), 201


if __name__ == '__main__':
    db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)
