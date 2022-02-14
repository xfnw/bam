import asyncio, time

from irctokens import build, Line
from ircrobots import Bot as BaseBot
from ircrobots import Server as BaseServer
from ircrobots import ConnectionParams

from secrets import OPER, NICK, NETWORK, HOST, SECONDS, MAXMSGS, JOIN


class Server(BaseServer):
    def __init__(self, bot, name):
        super().__init__(bot, name)
        self.log={}
    async def line_read(self, line):
        print(f"{self.name} < {line.format()}")
        if "on_" + line.command.lower() in dir(self):
            asyncio.create_task(
                self.__getattribute__("on_" + line.command.lower())(line)
            )

    async def line_send(self, line):
        print(f"{self.name} > {line.format()}")

    async def on_001(self, line):
        await self.send_raw(OPER)

    async def on_privmsg(self, line):
        nick = line.hostmask.nickname
        if nick not in self.log:
            self.log[nick] = []

        self.log[nick].append([time.now()] + line.params)
        if len(self.log[nick] > MAXMSGS):
            self.log[nick].pop(0)

        


class Bot(BaseBot):
    def create_server(self, name: str):
        return Server(self, name)


async def main():
    bot = Bot()

    params = ConnectionParams(NICK, host=HOST, port=6697, autojoin=JOIN)

    await bot.add_server(NETWORK, params)
    await bot.run()


if __name__ == "__main__":
    asyncio.run(main())
