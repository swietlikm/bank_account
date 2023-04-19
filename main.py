import getpass
import json
import os
import pathlib
import random
import re
import secrets
import string
import threading
from datetime import datetime

from bankAccountExceptions import (
    AccountAlreadyExistsException,
    AccountAlreadyLoggedException,
    AccountNotLoggedException,
    InvalidPasswordException,
)

SCRIPT_PATH = pathlib.Path(__file__).resolve().parent
DATABASE_FILE_NAME = "database.json"
DATABASE_PATH = pathlib.Path.joinpath(SCRIPT_PATH, DATABASE_FILE_NAME)


class Database:
    """
    Singleton representation of JSON Database with context manager
    Allows to load all data from database.
    Releasing all data within finish of context manager
    """

    _instance = None

    def __new__(cls):
        """Singleton representation in order to not create new instance of database"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_data()
        return cls._instance

    def __enter__(self):
        """load data upon enter into context manager"""
        return self._data

    def __exit__(self, exc_type, exc_val, exc_tb):
        """release memory upon exit of context manager"""
        pass

    def _load_data(self):
        """Load all data from database"""
        # Check if database file exists, if not -> create new one
        if not os.path.exists(DATABASE_PATH):
            with open(DATABASE_PATH, "w") as database:
                json.dump({}, database)

        # Load all data from database
        with open(DATABASE_PATH, "r", encoding="UTF-8") as database:
            self._data = json.load(database)

    def get_data(self):
        """Return all data from Bank database"""
        return self._data

    def get_accounts_ids(self):
        """Return all account_ids from database"""
        return self._data.keys()

    def get_accounts_numbers(self):
        """Return all account numbers from database"""
        return set(
            account.get("Account number", None) for account in self._data.values()
        )

    def save_data(self, data: dict):
        """Write data to the json database"""
        with open(DATABASE_PATH, "w", encoding="UTF-8") as database_file:
            json.dump(data, database_file)


class BankAccount:
    def __init__(self, account_id: str = None):
        """Initialize all variables associated to specific bank account ID"""
        self.__account_id = account_id
        self.__balance = 0  # Before logging the balance should be 0

        self.__first_name = None
        self.__last_name = None
        self.__ssn = None
        self.__account_number = None
        self.__created = None
        self.__modified = None

        self.__is_logged = False  # To perform transactions account must be logged with id and password to the bank account

        self.database = Database()  # Create an instance of connection to database
        self.lock = (
            threading.Lock()
        )  # Lock will prevent to perform multiple operations in the same time that are not allowed

    def update_database(self):
        """Update all account information to the Bank Database"""
        with self.database:
            data = self.database.get_data()
            account = data[self.__account_id]
            account["balance"] = self.__balance
            account["first_name"] = self.__first_name
            account["last_name"] = self.__last_name
            account["account_number"] = self.__account_number
            account["ssn"] = self.__ssn
            account["modified"] = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
            self.database.save_data(data)

    @property
    def is_logged(self) -> bool:
        return self.__is_logged

    @property
    def balance(self) -> bool:
        return self.__balance

    @property
    def first_name(self) -> bool:
        return self.__first_name

    def login(self, account_id: str) -> None:
        """Login to the BankAccount with the given credentials of id and password"""
        with self.database:
            account = self.database.get_data().get(account_id, None)

        # Check if given accound_id is in database
        if account is None:
            raise ValueError("Account doesn't exist")

        # Check if user input for password is the same as in database for specific account id
        password = getpass.getpass()
        if not secrets.compare_digest(account["password"], password):
            raise InvalidPasswordException

        # If credentials are valid then assign all instance variables from the database
        self.__account_id = account_id
        self.__first_name = account["first_name"]
        self.__last_name = account["last_name"]
        self.__ssn = account["ssn"]
        self.__balance = account["balance"]
        self.__account_number = account["account_number"]
        self.__is_logged = True
        print("\n>>> BANK >>>>>>>>>>>>>>>>>>>>>>")
        print(f"Welcome {self.first_name}, you are now logged in.")
        print(f"Your balance is: ${self.balance}")
        print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>\n")

    @staticmethod
    def is_password_validated(password1: str, password2=None) -> bool:
        """Function that check if user input for password fulfill all conditions. If the second argument is given then it check if both inputs are exactly the same"""
        PATTERN = r"(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()_+=\[{\]};:<>|./?,-])"

        # Check all conditions for the first input of password
        if password2 is None:
            if not len(password1) > 7:
                print("Password must be greater or eqaul to 8 characters")
                return False
            if not re.search(PATTERN, password1):
                print(
                    "Password must contain at least 1 upper case, 1 digit and 1 special character"
                )
                return False

        # Check if both inputs for passwords are the same
        else:
            if not secrets.compare_digest(password1, password2):
                print("Passwords do not match")
                return False
        return True

    def create(self) -> None:
        # Check if account is already logged. If it is logged, forbid the creating new account
        if self.is_logged:
            raise AccountAlreadyLoggedException

        account_id = input("Account ID: ")  # Ask user for account id (login)

        # Check if id already in database
        with self.database:
            if account_id in self.database.get_accounts_ids():
                raise AccountAlreadyExistsException

        # Ask and validate password
        password = getpass.getpass()
        while not self.is_password_validated(password):
            password = getpass.getpass()
        password_again = getpass.getpass("Repeat password: ")
        while not self.is_password_validated(password, password_again):
            password_again = getpass.getpass("Repeat password: ")

        # Generate account number
        account_number = None
        with self.database:
            while (
                account_number is None
                or account_number in self.database.get_accounts_numbers()
            ):
                account_number = "7810106666" + "".join(
                    random.choices(string.digits, k=16)
                )

        ######################
        # TODO: get all data like first name, last name, ssn
        ######################

        # Collect all data into dictionary
        new_account = {
            "password": password,
            "balance": 0,
            "account_number": account_number,
            "first_name": "",
            "last_name": "",
            "ssn": "",
            "created": datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
        }

        # Open database connection and add new account
        with self.database:
            data = self.database.get_data()
            data[account_id] = new_account
            self.database.save_data(data)
        print("Account created successfully!")

    def deposit(self, value: float) -> None:
        # Check if deposit value is valid
        if not self.is_logged:
            raise AccountNotLoggedException
        if not isinstance(value, (int, float)):
            raise TypeError("Value must be decimal")
        if value <= 0:
            raise ValueError("Deposit value must be greater than zero")

        # Perform deposit and update the database
        with self.lock:
            self.__balance += value
            self.update_database()


if __name__ == "__main__":
    my_account = BankAccount()
    # my_account.create()
    my_account.login(id="999")
    print(my_account.balance)
    my_account.deposit(50)
    print(my_account.balance)
