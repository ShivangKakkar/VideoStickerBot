from pystark import Stark
from database.users_sql import Users
# from httpx._multipart import format_form_param

# format_form_param()

bot = Stark()
Users.__table__.create(checkfirst=True)

if __name__ == "__main__":
    bot.activate()
