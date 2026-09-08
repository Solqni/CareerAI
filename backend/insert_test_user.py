import asyncio
import asyncpg
from app.core.config import settings
from app.core.security import hash_password

async def insert_test_user():
    """直接在数据库中插入测试用户"""
    try:
        # 连接到数据库
        conn = await asyncpg.connect(
            host=settings.POSTGRES_HOST,
            port=settings.POSTGRES_PORT,
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD,
            database=settings.POSTGRES_DB
        )

        print("成功连接到数据库")

        # 检查是否已有测试用户
        check_user = await conn.fetchrow(
            "SELECT COUNT(*) as count FROM \"user\" WHERE username = $1", "testuser"
        )

        if check_user['count'] > 0:
            print("用户 testuser 已存在，将删除后重新创建")
            # 删除现有用户
            await conn.execute("DELETE FROM \"user\" WHERE username = $1", "testuser")
            print("已删除现有用户")

        # 生成密码哈希 - 使用简单的哈希来避免bcrypt问题
        password = "test"
        # 使用bcrypt哈希
        password_hash = "$2b$12$GsN5qb2rc.odBQbuhtjujOwayP/lVeEW.nTGaXI3/fQ8BQrxq6Utu"
        print(f"密码哈希: {password_hash}")

        # 插入新用户
        result = await conn.execute(
            """
            INSERT INTO \"user\" (username, password_hash, email, role)
            VALUES ($1, $2, $3, $4)
            """,
            "testuser",
            password_hash,
            "test@example.com",
            "user"
        )

        print(f"插入结果: {result}")

        # 验证用户是否创建成功
        new_user = await conn.fetchrow(
            "SELECT username, email, role FROM \"user\" WHERE username = $1", "testuser"
        )

        if new_user:
            print("\nSUCCESS: 测试用户创建成功！")
            print(f"用户名: {new_user['username']}")
            print(f"邮箱: {new_user['email']}")
            print(f"角色: {new_user['role']}")
            print("\n你可以使用以下信息登录前端：")
            print("用户名: testuser")
            print("密码: test")
        else:
            print("ERROR: 用户创建失败")

        await conn.close()

    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(insert_test_user())