import pika
import json
import threading
import time
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Notification, NotificationType, NotificationPriority
from notification_service import NotificationService
from config import settings

class RabbitMQConsumer:
    
    def __init__(self):
        self.notification_service = NotificationService()
        self.connection = None
        self.channel = None
    
    def connect(self):
        """Establish connection to RabbitMQ"""
        self.connection = pika.BlockingConnection(
            pika.URLParameters(settings.RABBITMQ_URL)
        )
        self.channel = self.connection.channel()
        
        # Declare queues
        self.channel.queue_declare(queue='payment_notifications', durable=True)
        self.channel.queue_declare(queue='charter_notifications', durable=True)
        self.channel.queue_declare(queue='general_notifications', durable=True)
        
        # Set QoS - process one message at a time
        self.channel.basic_qos(prefetch_count=1)
    
    def process_payment_notification(self, ch, method, properties, body):
        """Process payment notification messages"""
        db = SessionLocal()
        try:
            message = json.loads(body)
            
            # Create notification based on payment status
            if message['status'] == 'succeeded':
                template_name = 'payment_success'
            elif message['status'] == 'failed':
                template_name = 'payment_failed'
            else:
                template_name = 'payment_processing'
            
            # Get charter/client info (would need to query from DB)
            # For now, create basic notification
            notification = Notification(
                notification_type=NotificationType.EMAIL,
                template_name=template_name,
                template_data=json.dumps(message),
                priority=NotificationPriority.HIGH,
                charter_id=message.get('charter_id'),
                payment_id=message.get('payment_id')
            )
            db.add(notification)
            db.commit()
            db.refresh(notification)
            
            # Send notification
            self.notification_service.send_notification(db, notification.id)
            
            # Acknowledge message
            ch.basic_ack(delivery_tag=method.delivery_tag)
            
        except Exception as e:
            print(f"Error processing payment notification: {e}")
            # Reject and requeue
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
        finally:
            db.close()
    
    def process_charter_notification(self, ch, method, properties, body):
        """Process charter notification messages"""
        db = SessionLocal()
        try:
            message = json.loads(body)
            
            notification = Notification(
                recipient_email=message.get('recipient_email'),
                recipient_phone=message.get('recipient_phone'),
                recipient_name=message.get('recipient_name'),
                notification_type=NotificationType[message.get('type', 'EMAIL').upper()],
                template_name=message.get('template_name'),
                template_data=json.dumps(message.get('data', {})),
                priority=NotificationPriority[message.get('priority', 'MEDIUM').upper()],
                charter_id=message.get('charter_id'),
                client_id=message.get('client_id')
            )
            db.add(notification)
            db.commit()
            db.refresh(notification)
            
            # Send notification
            self.notification_service.send_notification(db, notification.id)
            
            # Acknowledge message
            ch.basic_ack(delivery_tag=method.delivery_tag)
            
        except Exception as e:
            print(f"Error processing charter notification: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
        finally:
            db.close()
    
    def process_general_notification(self, ch, method, properties, body):
        """Process general notification messages"""
        db = SessionLocal()
        try:
            message = json.loads(body)
            
            notification = Notification(
                recipient_email=message.get('recipient_email'),
                recipient_phone=message.get('recipient_phone'),
                recipient_name=message.get('recipient_name'),
                notification_type=NotificationType[message.get('type', 'EMAIL').upper()],
                template_name=message.get('template_name'),
                template_data=json.dumps(message.get('data', {})),
                priority=NotificationPriority[message.get('priority', 'MEDIUM').upper()]
            )
            db.add(notification)
            db.commit()
            db.refresh(notification)
            
            # Send notification
            self.notification_service.send_notification(db, notification.id)
            
            # Acknowledge message
            ch.basic_ack(delivery_tag=method.delivery_tag)
            
        except Exception as e:
            print(f"Error processing general notification: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
        finally:
            db.close()
    
    def start_consuming(self):
        """Start consuming messages from all queues"""
        self.connect()
        
        # Set up consumers
        self.channel.basic_consume(
            queue='payment_notifications',
            on_message_callback=self.process_payment_notification
        )
        self.channel.basic_consume(
            queue='charter_notifications',
            on_message_callback=self.process_charter_notification
        )
        self.channel.basic_consume(
            queue='general_notifications',
            on_message_callback=self.process_general_notification
        )
        
        print("Starting RabbitMQ consumer...")
        try:
            self.channel.start_consuming()
        except KeyboardInterrupt:
            self.channel.stop_consuming()
            self.connection.close()
    
    def retry_worker(self):
        """Background worker to retry failed notifications"""
        while True:
            try:
                db = SessionLocal()
                self.notification_service.retry_failed_notifications(db)
                db.close()
            except Exception as e:
                print(f"Retry worker error: {e}")
            
            # Check every 60 seconds
            time.sleep(60)

def start_consumer():
    """Start the RabbitMQ consumer"""
    consumer = RabbitMQConsumer()
    
    # Start retry worker in background thread
    retry_thread = threading.Thread(target=consumer.retry_worker, daemon=True)
    retry_thread.start()
    
    # Start consuming messages
    consumer.start_consuming()

if __name__ == "__main__":
    start_consumer()
