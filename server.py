import websockets
import asyncio

class Server:
    def __init__(self):
        self.conn_clients = []


    async def connect(self, websocket, path):
        # Realiza a conexão do client (inicializa),
        # adiciona o novo cliente à lista de conexões.

        client = Client(self, websocket, path)      # Cria client
        if client not in self.conn_clients:         # Se for client novo é adicionado à lista
            self.conn_clients.append(client)
            print("Novo cliente conectado!")
            print("Número de conexões:", len(self.conn_clients))
        await client.handler()


    async def disconnect(self, client):
        # Remove o client desejado e informa o número de conexões restantes 

        if client in self.conn_clients:
            self.conn_clients.remove(client)
            print(f"Cliente '{client.name}' desconectado!")
        else: 
            print("Não foi possível desfazer a conexão.")

        print("Número de conexões:", len(self.conn_clients))


    async def verify_name(self, name):
        # Verifica se o nome já existe. Se existe retorna falso

        for client in self.conn_clients:
            if client.name and client.name == name:
                return False
        return True


    async def send_all(self, sender, msg):
        # Envia a mensagem para todos os clients conectados

        for client in self.conn_clients:
            if sender != client and client.client.open:
                await client.client.send(f"{sender.name} >> {msg}")


    async def send_destination(self, sender, msg, receiver):

        for client in self.conn_clients:
            if sender != client and client.client.open and client.name == receiver:
                await client.client.send(f"{sender.name} >> {msg}")
                return True
        return False



# ====================================================================================== #

class Client:
    def __init__(self, server, websocket, path):
        self.name = None
        self.server = server
        self.client = websocket


    async def handler(self):
        # Recebe inputs e trata
         
        try:
            await self.client.send("Defina seu nome de usuário com /name SeuNome.")
            await self.client.send("Comandos: /name e /sendpv")

            while True:
                data = await self.client.recv()
                if data:
                    print(f"{self.name} < {data}")
                    await self.process_command(data)
                else:
                    break

        except Exception:
            print("Erro!")
            raise

        finally:
            self.server.disconnect(self)

    
    async def process_command(self, data):
        # Processa o que for comando (inicia com /) e 

        msg = data.split()
        if msg[0][0] == '/':                            # É comando

            comando = msg[0][1:]                        # Primeira série de caracteres sem o primeiro caracter 

            if comando == 'name':                       # Comando para mudar nome
                await self.change_name(msg)
            elif comando == 'sendpv':                   # Comando para enviar mensagem privada
                await self.send_pv(msg)
            else:                                       # Comando inválido
                self.client.send("Comando inválido") 
        else:
            if self.name:
                await self.server.send_all(self, data)
            else:
                await self.client.send("Se identifique com /name SeuNome antes de enviar mensagem")

    async def change_name(self, content):
        # Altera o nome caso seja um nome válido

        if (len(content) <= 1) or (len(content) > 2):
            await self.client.send("Erro! Use /name SeuNome.")
        elif self.server.verify_name(content[1]):
            self.name = content[1]
            await self.client.send(f"Nome alterado para {self.name}")
            await self.server.send_all(self, f"{self.name} entrou no chat ...")
        else:
            await self.client.send("Já existe um usuário com este nome ...")

    async def send_pv(self, content):
        #

        if (len(content) <= 2):
            await self.client.send("Erro! Use /sendpv Destinatario Mensagem")
        else:
            receiver = content[1]
            msg = " ".join(content[2:])
            sent = await self.server.send_destination(self, msg, receiver)

            if not sent:
                await self.client.send("Erro! Destinatário não encontrado")


server = Server() 
loop = asyncio.get_event_loop()
start_server = websockets.serve(server.connect, 'localhost', 8888) 

loop.run_until_complete(start_server)
loop.run_forever()