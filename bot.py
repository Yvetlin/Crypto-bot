import os
import disnake
from disnake.ext import commands
from idea import IDEA

#Нерабочая либа
def load_env_file(file_path):
    with open(file_path) as f:
        for line in f:
            # Убираем комментарии и пустые строки
            line = line.strip()
            if line and not line.startswith('#'):
                # Разбиваем строку на ключ и значение
                key, value = line.split('=', 1)
                # Убираем возможные пробелы и кавычки вокруг значений
                key = key.strip()
                value = value.strip().strip('\'"')
                # Устанавливаем переменные окружения
                os.environ[key] = value

# Указываем путь к .env файлу
env_file_path = '.env'

# Загружаем переменные из .env файла
load_env_file(env_file_path)

# Создаем экземпляр бота с включенным намерением для доступа к содержимому сообщений
intents = disnake.Intents.default()
intents.message_content = True  # Включаем доступ к содержимому сообщений

bot = commands.Bot(command_prefix='/', intents=intents)

# Команда /test
@bot.slash_command(description="Test command")
async def test(interaction: disnake.ApplicationCommandInteraction):
    # Отправляем сообщение автору команды в личку
    author = interaction.author
    await author.send("Пипипу")
    # Уведомляем пользователя в канале о выполнении команды
    await interaction.response.send_message("Сообщение отправлено в личку!", ephemeral=True)

# Команда /crypt
@bot.slash_command(description="Encrypt or Decrypt a message")
async def crypt(
    interaction: disnake.ApplicationCommandInteraction,
    mode: str = commands.Param(choices=["encrypt", "decrypt"]),
    text: str = commands.Param(description="Text to encrypt or decrypt"),
    key: str = commands.Param(description="Encryption key in hex format (optional)", default=None)
):
    # Используем ключ по умолчанию, если пользователь не предоставил свой
    if key is None:
        key = "6E3272357538782F413F4428472B4B62"

    # Преобразование ключа из hex в int
    try:
        key_int = int(key, 16)
    except ValueError:
        await interaction.response.send_message("Invalid key format! Please provide a valid hex key.", ephemeral=True)
        return

    # Создание экземпляра IDEA с ключом
    my_idea = IDEA(key_int)

    if mode == "encrypt":
        # Преобразование текста в формат int
        plain = int.from_bytes(text.encode("ASCII"), 'big')
        size = plain.bit_length()

        sub_plain = []
        sub_enc = []
        x = size // 64
        if size % 64 != 0:
            x += 1
            size += 64 - size % 64
        for i in range(x):
            shift = size - (i + 1) * 64
            sub_plain.append((plain >> shift) & 0xFFFFFFFFFFFFFFFF)
            encrypted = my_idea.encrypt(sub_plain[i])
            sub_enc.append(encrypted)
            encrypted = 0
        for i in range(x):
            sub_enc[i] = sub_enc[i] << (x - (i + 1)) * 64
            encrypted = encrypted | sub_enc[i]

        await interaction.response.send_message(f"Encrypted: {hex(encrypted)}", ephemeral=True)

    elif mode == "decrypt":
        try:
            # Преобразование текста из hex в int
            encrypted = int(text, 16)
        except ValueError:
            await interaction.response.send_message("Invalid ciphertext format! Please provide hex.", ephemeral=True)
            return

        sub_dec = []
        size = encrypted.bit_length()
        if size % 64 != 0:
            x = size // 64 + 1
            size += 64 - size % 64
        else:
            x = size // 64
        decrypted = 0
        for i in range(x):
            shift = size - (i + 1) * 64
            k = (encrypted >> shift) & 0xFFFFFFFFFFFFFFFF
            sub_dec.append(my_idea.decrypt(k))
        for i in range(x):
            sub_dec[i] = sub_dec[i] << (x - (i + 1)) * 64
            decrypted = decrypted | sub_dec[i]

        decrypted_text = decrypted.to_bytes(64, 'big').decode('ASCII', errors='ignore')
        await interaction.response.send_message(f"Decrypted: {decrypted_text} (hex: {hex(decrypted)})", ephemeral=True)

# Запуск бота
bot.run(os.environ.get('TOKEN'))
