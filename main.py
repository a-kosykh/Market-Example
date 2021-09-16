import sqlite3
import hashlib
import bcrypt


class AuthDatabase:
    def __init__(self, name):
        self.name = name
        self.conn = None

    def create_connection(self):
        try:
            self.conn = sqlite3.connect(self.name)
        except sqlite3.OperationalError as e:
            print(e)

    def create_table(self):
        try:
            c = self.conn.cursor()
            c.execute("CREATE TABLE IF NOT EXISTS users"
                      "(username text NOT NULL,"
                      "h_password text,"
                      "salt text);")
            c.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_username ON users (username);")
        except sqlite3.Error as e:
            print(e)

    def show_table(self):
        try:
            c = self.conn.cursor()
            c.execute("SELECT * FROM users")
            rows = c.fetchall()

            for row in rows:
                print(row)

        except sqlite3.Error as e:
            print(e)

    def register_user(self, data):
        try:
            c = self.conn.cursor()
            sql_query = ''' INSERT INTO users(username, h_password, salt) VALUES (?,?,?) '''
            c.execute(sql_query, data)
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            return False

    def get_salt(self, name):
        try:
            c = self.conn.cursor()
            sql_query = ''' SELECT salt FROM users WHERE username = ? '''
            c.execute(sql_query, name)
            self.conn.commit()

            return c.fetchone()[0]
        except sqlite3.Error as e:
            print(e)
            return False

    def find_user(self, data):
        c = self.conn.cursor()
        sql_query = ''' SELECT * FROM users WHERE username = ? AND h_password = ? '''
        c.execute(sql_query, data)

        rows = c.fetchall()
        if len(rows) > 0:
            return True
        else:
            return False

    def update_password(self, data):
        try:
            c = self.conn.cursor()
            sql_query = ''' UPDATE users SET h_password = ?, salt = ? WHERE username = ? '''
            c.execute(sql_query, data)
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print("update password: ", e)
            return False


class Auth:
    def __init__(self, db_obj, max_attempts):
        self.db = db_obj
        self.logged_user = None
        self.login_attempts = 0
        self.max_attempts = max_attempts

    def register(self, name, password):
        if self.db is not None:
            salt = bcrypt.gensalt()
            print("salt: ", salt)
            h_password = hashlib.pbkdf2_hmac('sha256', bytes(password, 'utf-8'), salt, 100000).hex()
            if self.db.register_user((name, h_password, salt)):
                print(f"Успешная регистрация '{name}'!")
            else:
                print(f"ОШИБКА: Пользователь '{name}' уже существует!")

    def login_limit(self):
        if self.login_attempts == self.max_attempts:
            print("Максимальное количество попыток входа!")
            return True
        else:
            return False

    def login(self, name, password):

        if self.login_limit():
            return False

        salt = self.db.get_salt((name,))

        h_password = hashlib.pbkdf2_hmac('sha256', bytes(password, 'utf-8'), salt, 100000).hex()
        if self.db.find_user((name, h_password)):
            print(f"Успешный вход!")
            self.logged_user = User(name)
            return True
        else:
            print(f"Неверный логин или пароль!")
            self.login_attempts += 1
            return False

    def change_password(self, prev_password, new_password):
        if self.logged_user is None:
            return

        salt = self.db.get_salt((self.logged_user.name,))
        h_prev_password = hashlib.pbkdf2_hmac('sha256', bytes(prev_password, 'utf-8'), salt, 100000).hex()
        if self.db.find_user((self.logged_user.name, h_prev_password)):
            new_salt = bcrypt.gensalt()
            h_new_password = hashlib.pbkdf2_hmac('sha256', bytes(new_password, 'utf-8'), new_salt, 100000).hex()
            if self.db.update_password((h_new_password, new_salt, self.logged_user.name,)):
                print("Пароль обновлен!")
        else:
            print("ОШИБКА: Неверный старый пароль")


class Product:
    def __init__(self, name, price, desc):
        self.name = name
        self.price = price
        self.desc = desc


class Position:
    def __init__(self, product, amount):
        self.product = product
        self.amount = amount


class Order:
    def __init__(self, id_):
        self.id = id_
        self.products = []
        self.isPaid = False

    def addProduct(self, product):
        self.products.append(product)


class User:
    def __init__(self, name):
        self.name = name
        self.orders = []

    def addOrder(self, order):
        self.orders.append(order)


class MarketDatabase:
    def __init__(self):
        self.__positions = []
        self.__users = []
        self.__orders = []

    def addPosition(self, position):
        self.__positions.append(position)

    def addOrder(self, order):
        self.__orders.append(order)

    def addUser(self, user):
        self.__users.append(user)

    def nextOrderId(self):
        return len(self.__orders)

    def getPositionsShort(self):
        if len(self.__positions) == 0:
            print("Нет позиций")
            return

        print("Наименование - Цена")
        for position in self.__positions:
            print(position.product.name, f"{position.product.price} руб.")

    def getPositions(self):
        if len(self.__positions) == 0:
            print("No products")
            return

        print("Наименование - Цена - Количество - Описание")
        for position in self.__positions:
            print(position.product.name, f"{position.product.price} руб.", position.amount, f"{position.product.desc}")

    def getProduct(self, name):
        for position in self.__positions:
            if position.product.name == name:
                return position.product
        return None

    def getOrder(self, order_id):
        for order in self.__orders:
            if order.id == order_id:
                return order
        return None

    def printOrder(self, order_id):
        for order in self.__orders:
            if order.id == order_id:
                print(f"Заказ {order_id}: ")
                if order.isPaid:
                    print("Оплачен")
                else:
                    print("Не оплачен!")
                print("Наименование - Цена")
                fullPrice = 0
                for product in order.products:
                    fullPrice += product.price
                    print(product.name, f"{product.price} руб.")
                print(f"Заказ на сумму: {fullPrice} руб.")
                break

    def createOrder(self, user, products):
        order = Order(self.nextOrderId())
        for product in products:
            for position in self.__positions:
                if product.name == position.product.name:
                    if position.amount - 1 < 0:
                        return
                    order.addProduct(product)
                    position.amount -= 1

        self.__orders.append(order)
        user.addOrder(order)
        print("Заказ создан....")

    def addToOrder(self, order_id, product):
        order = self.getOrder(order_id)
        for position in self.__positions:
            if product.name == position.product.name:
                if position.amount - 1 < 0:
                    return
                order.addProduct(product)
                position.amount -= 1
                break
        print(f"В заказ {order.id} добавлен {product.name}")

    def payForOrder(self, order_id):
        order = self.getOrder(order_id)
        order.isPaid = True
        print(f"Заказ {order_id} успешно оплачен!")


def fillProducts(db):
    print("Добавляем позиции в БД........")
    db.addPosition(Position(Product("Футболка", 2000, ""), 3))
    db.addPosition(Position(Product("Рубашка", 3000, ""), 2))
    db.addPosition(Position(Product("Куртка", 6000, ""), 2))
    db.addPosition(Position(Product("Пиджак", 5000, ""), 2))


def init_loop(auth):
    db = MarketDatabase()
    db.addUser(auth.logged_user)

    print(f"\nYour are logged as {auth.logged_user.name}...")
    while True:
        command = input("**********  Enter command: ")
        if command == 'exit':
            break
        if command == 'show_table':
            auth.db.show_table()
        if command == 'change_password':
            prev_password = input("Enter prev password: ")
            new_password = input("Enter new password: ")
            new_password_2 = input("Enter new password again: ")
            if new_password != new_password_2:
                continue

            auth.change_password(prev_password, new_password)

        if command == '1':
            fillProducts(db)
            db.getPositions()
            print("\n")

            db.createOrder(auth.logged_user,
                           [db.getProduct("Рубашка"), db.getProduct("Пиджак")]
                           )
            print("\n")
            db.getPositions()
            print("\n")

            db.addToOrder(0, db.getProduct("Пиджак"))
            print("\n")
            db.getPositions()
            print("\n")

            db.printOrder(0)
            print("\n")

            db.payForOrder(0)
            print("\n")

            db.printOrder(0)




def main():
    db_name = "mydb.db"

    db = AuthDatabase(db_name)
    db.create_connection()

    if db.conn is not None:
        db.create_table()
    else:
        return -1

    auth = Auth(db, 3)

    while True:
        code = input("\nAuthorization soft\n1>Register\n2>Login\n3>Exit\nEnter code: ")
        if code == '1':
            print("\n---Registration---")
            name = input("Enter username: ")
            password = input("Enter password: ")
            auth.register(name, password)
            continue

        if code == '2':
            print("\n---Login---")
            name = input("Enter username: ")
            password = input("Enter password: ")
            if auth.login(name, password):
                init_loop(auth)
                break
            continue

        if code == '3':
            print("\nExiting....")
            break


if __name__ == "__main__":
    main()
