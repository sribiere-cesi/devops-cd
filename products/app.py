from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
import pika
import json


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://user:password@products-db:3306/products'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

def callback(ch, method, properties, body):
    print(f"Received {body}")
    order_details = json.loads(body)
    product = Product.query.get(order_details['product_id'])
    if product and product.quantity >= order_details['quantity']:
        print("Produit disponible")
        # Mettre à jour le stock ou toute autre logique métier
    else:
        print("Produit non disponible")

connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
channel = connection.channel()
channel.queue_declare(queue='order_queue')
channel.basic_consume(queue='order_queue', on_message_callback=callback, auto_ack=True)

print(' [*] Waiting for messages. To exit press CTRL+C')
channel.start_consuming()


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)

    def to_json(self):
        return {"id": self.id, "name": self.name, "price": self.price}

@app.route('/products', methods=['GET'])
def get_products():
    products = Product.query.all()
    return jsonify([product.to_json() for product in products])

@app.route('/products', methods=['POST'])
def add_product():
    data = request.get_json()
    new_product = Product(name=data['name'], price=data['price'])
    db.session.add(new_product)
    db.session.commit()
    return jsonify(new_product.to_json()), 201



if __name__ == '__main__':
    db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)
