import aiosqlite
from datetime import datetime, timedelta

DB_NAME = "bot_database.db"


async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                is_blocked BOOLEAN DEFAULT FALSE,
                penalty_amount INTEGER DEFAULT 0,
                penalty_order_id INTEGER DEFAULT 0
            )
        """)
        # ДОБАВЛЕНО ПОЛЕ complexity (сложность)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                complexity TEXT,
                bot_type TEXT,
                task TEXT,
                budget TEXT,
                price INTEGER DEFAULT 0,
                status TEXT DEFAULT 'new',
                discount_applied BOOLEAN DEFAULT FALSE,
                friend_id INTEGER DEFAULT 0,
                delivered_at TEXT DEFAULT NULL,
                created_at TEXT DEFAULT NULL
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS portfolio (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                description TEXT,
                photo_id TEXT,
                link TEXT
            )
        """)
        await db.commit()


async def add_user(user_id: int, username: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", (user_id, username))
        await db.commit()


async def get_user_block_info(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT is_blocked, penalty_amount, penalty_order_id FROM users WHERE user_id = ?",
                                  (user_id,))
        res = await cursor.fetchone()
        if res:
            return bool(res[0]), res[1], res[2]
        return False, 0, 0


async def block_user(user_id: int, status: bool = True, penalty: int = 0, order_id: int = 0):
    async with aiosqlite.connect(DB_NAME) as db:
        if status:
            await db.execute(
                "UPDATE users SET is_blocked = ?, penalty_amount = ?, penalty_order_id = ? WHERE user_id = ?",
                (status, penalty, order_id, user_id))
        else:
            await db.execute(
                "UPDATE users SET is_blocked = FALSE, penalty_amount = 0, penalty_order_id = 0 WHERE user_id = ?",
                (user_id,))
        await db.commit()


# ОБНОВЛЕНО: добавлена сложность
async def create_order(user_id: int, complexity: str, bot_type: str, task: str, budget: str) -> int:
    now_str = datetime.now().isoformat()
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "INSERT INTO orders (user_id, complexity, bot_type, task, budget, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, complexity, bot_type, task, budget, now_str)
        )
        await db.commit()
        return cursor.lastrowid


async def get_user_orders(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT id, bot_type, task, price, status, created_at FROM orders WHERE user_id = ? ORDER BY id DESC",
            (user_id,))
        return await cursor.fetchall()


async def get_order(order_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
        return await cursor.fetchone()


async def update_order_status(order_id: int, status: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))
        await db.commit()


async def delete_order(order_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("DELETE FROM orders WHERE id = ?", (order_id,))
        await db.commit()


async def set_order_price(order_id: int, price: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE orders SET price = ?, status = 'waiting_payment' WHERE id = ?", (price, order_id))
        await db.commit()


async def deliver_order(order_id: int):
    now_str = datetime.now().isoformat()
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE orders SET status = 'done', delivered_at = ? WHERE id = ?", (now_str, order_id))
        await db.commit()


async def get_orders_to_check():
    check_date = (datetime.now() - timedelta(days=7)).isoformat()
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT id, user_id, friend_id, price FROM orders WHERE status = 'done' AND delivered_at <= ? AND friend_id != 0",
            (check_date,)
        )
        return await cursor.fetchall()


async def apply_referral(order_id: int, friend_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT price FROM orders WHERE id = ?", (order_id,))
        res = await cursor.fetchone()
        if res and res[0] > 0:
            new_price = int(res[0] * 0.9)
            await db.execute("UPDATE orders SET price = ?, discount_applied = TRUE, friend_id = ? WHERE id = ?",
                             (new_price, friend_id, order_id))
            await db.commit()
            return new_price
    return None


async def get_all_new_orders():
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT id, user_id, complexity, bot_type, task, budget FROM orders WHERE status = 'new'")
        return await cursor.fetchall()


async def get_all_orders():
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT id, user_id, complexity, bot_type, task, price, status FROM orders ORDER BY id DESC")
        return await cursor.fetchall()


async def get_stats():
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM users")
        users_count = (await cursor.fetchone())[0]
        cursor = await db.execute("SELECT COUNT(*) FROM orders")
        orders_count = (await cursor.fetchone())[0]
        cursor = await db.execute("SELECT SUM(price) FROM orders WHERE status = 'done'")
        total_earned = (await cursor.fetchone())[0] or 0
        return users_count, orders_count, total_earned


async def get_all_users():
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT user_id FROM users WHERE is_blocked = FALSE")
        return await cursor.fetchall()


async def add_portfolio(title: str, desc: str, photo_id: str, link: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("INSERT INTO portfolio (title, description, photo_id, link) VALUES (?, ?, ?, ?)",
                         (title, desc, photo_id, link))
        await db.commit()


async def get_portfolio():
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT id, title, description, photo_id, link FROM portfolio ORDER BY id DESC")
        return await cursor.fetchall()


async def delete_portfolio(item_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("DELETE FROM portfolio WHERE id = ?", (item_id,))
        await db.commit()
