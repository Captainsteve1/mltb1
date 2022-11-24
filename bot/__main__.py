from signal import signal, SIGINT
from os import path as ospath, remove as osremove, execl as osexecl
from subprocess import run as srun
from psutil import disk_usage, cpu_percent, swap_memory, cpu_count, virtual_memory, net_io_counters, boot_time
from time import time
from sys import executable
from telegram.ext import CommandHandler

from bot import bot, dispatcher, updater, botStartTime, IGNORE_PENDING_REQUESTS, LOGGER, Interval, \
                DATABASE_URL, app, main_loop, QbInterval, INCOMPLETE_TASK_NOTIFIER, STOP_DUPLICATE_TASKS
from bot.helper.ext_utils.fs_utils import start_cleanup, clean_all, exit_clean_up
from bot.helper.ext_utils.bot_utils import get_readable_file_size, get_readable_time, set_commands
from bot.helper.ext_utils.db_handler import DbManger
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.message_utils import sendMessage, sendMarkup, editMessage, sendLogFile
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.button_build import ButtonMaker
from bot.modules import authorize, drive_list, cancel_mirror, mirror_status, mirror_leech, clone, users_settings, ytdlp, \
                        shell, eval, delete, count, search, rss, bt_select, rmdb, bot_settings, bot_updater, save_message, category_select
from bot.helper.ext_utils.jmdkh_utils import send_changelog
from telegram.utils.helpers import mention_html
from bot.version import __version__

def stats(update, context):
    total, used, free, disk = disk_usage('/')
    swap = swap_memory()
    memory = virtual_memory()
    stats = f'<b>Version</b>: {__version__}\n\n'\
            f'<b>Bot Uptime</b>: {get_readable_time(time() - botStartTime)}\n'\
            f'<b>OS Uptime</b>: {get_readable_time(time() - boot_time())}\n\n'\
            f'<b>Total Disk Space </b>: {get_readable_file_size(total)}\n'\
            f'<b>Used</b>: {get_readable_file_size(used)} | <b>Free</b>: {get_readable_file_size(free)}\n\n'\
            f'<b>Upload</b>: {get_readable_file_size(net_io_counters().bytes_sent)}\n'\
            f'<b>Download</b>: {get_readable_file_size(net_io_counters().bytes_recv)}\n\n'\
            f'<b>CPU</b>: {cpu_percent(interval=0.5)}%\n'\
            f'<b>RAM</b>: {memory.percent}%\n'\
            f'<b>DISK</b>: {disk}%\n\n'\
            f'<b>Physical Cores</b>: {cpu_count(logical=False)}\n'\
            f'<b>Total Cores</b>: {cpu_count(logical=True)}\n\n'\
            f'<b>SWAP</b>: {get_readable_file_size(swap.total)} | <b>Used</b>: {swap.percent}%\n'\
            f'<b>Memory Total</b>: {get_readable_file_size(memory.total)}\n'\
            f'<b>Memory Free</b>: {get_readable_file_size(memory.available)}\n'\
            f'<b>Memory Used</b>: {get_readable_file_size(memory.used)}\n'
    sendMessage(stats, context.bot, update.message)

def start(update, context):
    buttons = ButtonMaker()
    buttons.buildbutton("📢 Channel", 'https://t.me/JMDKH_Team')
    reply_markup = buttons.build_menu(1)
    uname = mention_html(update.message.from_user.id, update.message.from_user.first_name)
    if CustomFilters.authorized_user(update) or CustomFilters.authorized_chat(update):
        start_string = f'🙌🏽Hey <b>{uname}</b>\n\n' \
        '🌹 Welcome To One Of A Modified Anas Mirror Bot\n' \
        'This bot can Mirror all your links To Google Drive!\n' \
        '👨🏽‍💻 Powered By: @tmirrorleechupdates'
        sendMarkup(start_string, context.bot, update.message, reply_markup)
    else:
        sendMarkup('Not Authorized user', context.bot, update.message, reply_markup)
def restart(update, context):
    restart_message = sendMessage("Restarting...", context.bot, update.message)
    if Interval:
        Interval[0].cancel()
        Interval.clear()
    if QbInterval:
        QbInterval[0].cancel()
        QbInterval.clear()
    clean_all()
    srun(["pkill", "-9", "-f", "gunicorn|aria2c|qbittorrent-nox|ffmpeg"])
    srun(["python3", "update.py"])
    with open(".restartmsg", "w") as f:
        f.truncate(0)
        f.write(f"{restart_message.chat.id}\n{restart_message.message_id}\n")
    osexecl(executable, executable, "-m", "bot")


def ping(update, context):
    start_time = int(round(time() * 1000))
    reply = sendMessage("Starting Ping", context.bot, update.message)
    end_time = int(round(time() * 1000))
    editMessage(f'{end_time - start_time} ms', reply)


def log(update, context):
    sendLogFile(context.bot, update.message)

help_string = f'''
NOTE: Try each command without any perfix to see more detalis.
/{BotCommands.MirrorCommand[0]} or /{BotCommands.MirrorCommand[1]}: Start mirroring/leeching to Google Drive.
/{BotCommands.YtdlCommand[0]} or /{BotCommands.YtdlCommand[1]}: Mirror/Leech yt-dlp supported link.
/{BotCommands.CloneCommand} [drive_url]: Copy file/folder to Google Drive.
/{BotCommands.CountCommand} [drive_url]: Count file/folder of Google Drive.
/{BotCommands.DeleteCommand} [drive_url]: Delete file/folder from Google Drive (Only Owner & Sudo).
/{BotCommands.UserSetCommand} : Users settings.
/{BotCommands.BtSelectCommand}: Select files from torrents by gid or reply.
/{BotCommands.CategorySelect}: Change upload category for Google Drive.
/{BotCommands.CancelMirror}: Cancel task by gid or reply.
/{BotCommands.CancelAllCommand} : Cancel all tasks which added by you.
/{BotCommands.ListCommand[0]} [query]: Search in Google Drive(s).
/{BotCommands.SearchCommand} [query]: Search for torrents with API.
/{BotCommands.StatusCommand[0]} or /{BotCommands.StatusCommand[1]}: Shows a status of all the downloads.
/{BotCommands.StatsCommand}: Show stats of the machine where the bot is hosted in.
/{BotCommands.PingCommand[0]} or /{BotCommands.PingCommand[1]}: Check how long it takes to Ping the Bot (Only Owner & Sudo).
/{BotCommands.AuthorizeCommand}: Authorize a chat or a user to use the bot (Only Owner & Sudo).
/{BotCommands.UnAuthorizeCommand}: Unauthorize a chat or a user to use the bot (Only Owner & Sudo).
/{BotCommands.UsersCommand}: show users settings (Only Owner & Sudo).
/{BotCommands.AddSudoCommand}: Add sudo user (Only Owner).
/{BotCommands.RmSudoCommand}: Remove sudo users (Only Owner).
/{BotCommands.RestartCommand}: Restart and update the bot (Only Owner & Sudo).
/{BotCommands.LogCommand}: Get a log file of the bot. Handy for getting crash reports (Only Owner & Sudo).
/{BotCommands.ShellCommand}: Run shell commands (Only Owner).
/{BotCommands.EvalCommand}: Run Python Code Line | Lines (Only Owner).
/{BotCommands.ExecCommand}: Run Commands In Exec (Only Owner).
/{BotCommands.ClearLocalsCommand}: Clear {BotCommands.EvalCommand} or {BotCommands.ExecCommand} locals (Only Owner).
'''

def bot_help(update, context):
    sendMessage(help_string, context.bot, update.message)

def main():
    set_commands(bot)
    start_cleanup()
    if DATABASE_URL and STOP_DUPLICATE_TASKS:
        DbManger().clear_download_links()
    if INCOMPLETE_TASK_NOTIFIER and DATABASE_URL:
        if notifier_dict:= DbManger().get_incomplete_tasks():
            for cid, data in notifier_dict.items():
                if ospath.isfile(".restartmsg"):
                    with open(".restartmsg") as f:
                        chat_id, msg_id = map(int, f)
                    msg = 'Restarted Successfully!'
                else:
                    msg = 'Bot Restarted!'
                for tag, links in data.items():
                    msg += f"\n\n{tag}: "
                    for index, link in enumerate(links, start=1):
                        msg += f" <a href='{link}'>{index}</a> |"
                        if len(msg.encode()) > 4000:
                            if 'Restarted Successfully!' in msg and cid == chat_id:
                                try:
                                    bot.editMessageText(msg, chat_id, msg_id, parse_mode='HTML', disable_web_page_preview=True)
                                except:
                                    pass
                                osremove(".restartmsg")
                            else:
                                try:
                                    bot.sendMessage(cid, msg, parse_mode='HTML', disable_web_page_preview=True)
                                except Exception as e:
                                    LOGGER.error(e)
                            msg = ''
                if 'Restarted Successfully!' in msg and cid == chat_id:
                    try:
                        bot.editMessageText(msg, chat_id, msg_id, parse_mode='HTML', disable_web_page_preview=True)
                    except:
                        pass
                    osremove(".restartmsg")
                else:
                    try:
                        bot.sendMessage(cid, msg, parse_mode='HTML', disable_web_page_preview=True)
                    except Exception as e:
                        LOGGER.error(e)
    if ospath.isfile(".restartmsg"):
        with open(".restartmsg") as f:
            chat_id, msg_id = map(int, f)
        try:
            bot.edit_message_text("Restarted Successfully!", chat_id, msg_id)
        except:
            pass
        osremove(".restartmsg")

    send_changelog(bot, __version__)

    start_handler = CommandHandler(BotCommands.StartCommand, start, run_async=True)
    log_handler = CommandHandler(BotCommands.LogCommand, log,
                                        filters=CustomFilters.owner_filter | CustomFilters.sudo_user, run_async=True)
    restart_handler = CommandHandler(BotCommands.RestartCommand, restart,
                                        filters=CustomFilters.owner_filter | CustomFilters.sudo_user, run_async=True)
    ping_handler = CommandHandler(BotCommands.PingCommand, ping,
                               filters=CustomFilters.authorized_chat | CustomFilters.authorized_user, run_async=True)
    help_handler = CommandHandler(BotCommands.HelpCommand, bot_help,
                               filters=CustomFilters.authorized_chat | CustomFilters.authorized_user, run_async=True)
    stats_handler = CommandHandler(BotCommands.StatsCommand, stats,
                               filters=CustomFilters.authorized_chat | CustomFilters.authorized_user, run_async=True)

    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(ping_handler)
    dispatcher.add_handler(restart_handler)
    dispatcher.add_handler(help_handler)
    dispatcher.add_handler(stats_handler)
    dispatcher.add_handler(log_handler)

    updater.start_polling(drop_pending_updates=IGNORE_PENDING_REQUESTS)
    LOGGER.info("Bot Started!")
    signal(SIGINT, exit_clean_up)

app.start()
main()
main_loop.run_forever()
