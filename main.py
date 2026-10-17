import discord
from discord.ext import commands, tasks
import datetime
import asyncio

# === CONFIGURAÇÃO DO BOT ===
# Insira o Token do seu Bot entre as aspas abaixo (Passo 4 do guia anterior)
TOKEN = MTU2MDg2Njc1OTI3NDEzOTY2OA.Gt0v5w.W_MmmbCzScmi0VA3tYHUQWYFWY9q0K8lmnF3KI


# Lista de todos os horários do seu Diário Solo (Tirei das fotos que você mandou)
HORARIOS_DIARIO = [
    "13:00", "13:30", "14:00", "14:30", "15:00", "15:30",
    "16:00", "16:30", "17:00", "17:30", "18:00", "18:30"
]

# Banco de dados temporário na memória para guardar as inscrições
# Estrutura: { "horario": { user_id: "id_do_jogador" } }
inscritos_por_horario = {horario: {} for horario in HORARIOS_DIARIO}

# Armazenamento das Salas (ID e Senha) que o ADM vai cadastrar
# Estrutura: { "horario": "ID: 12345 | Senha: 999" }
salas_cadastradas = {horario: None for horario in HORARIOS_DIARIO}

class CadastroIDModal(discord.ui.Modal, title="Inscrição na Liga Diário"):
    id_jogador = discord.ui.TextInput(
        label="Digite seu ID do Free Fire:", 
        placeholder="Ex: 58291048", 
        min_length=5, 
        max_length=15,
        required=True
    )
    
    def __init__(self, horario):
        super().__init__()
        self.horario = horario

    async def on_submit(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        player_id = self.id_jogador.value
        
        # Salva o jogador no horário escolhido
        inscritos_por_horario[self.horario][user_id] = player_id
        
        await interaction.response.send_message(
            f"✅ **Você está inscrito!**\n⏰ Horário: **{self.horario}**\n🎮 ID Registrado: `{player_id}`\n\n*Você receberá um aviso aqui no privado 30 minutos antes da partida.*", 
            ephemeral=True
        )

class MenuHorarios(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label=f"Liga Diário | {h}", value=h, emoji="🏆") 
            for h in HORARIOS_DIARIO
        ]
        super().__init__(placeholder="👉 Escolha um horário para jogar...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        horario_escolhido = self.values[0]
        # Abre a caixinha pop-up para o jogador digitar o ID do Free Fire
        await interaction.response.send_modal(CadastroIDModal(horario_escolhido))

class VisualizacaoMenu(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None) # Mantém o menu funcionando para sempre
        self.add_item(MenuHorarios())

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"🤖 Bot {bot.user} iniciado com sucesso!")
    verificar_cronometro.start()

@bot.command()
@commands.has_permissions(administrator=True)
async def postar_diario(ctx):
    """Comando para o ADM postar a tabela oficial com o menu no canal"""
    embed = discord.Embed(
        title="🏆 LIGA DIÁRIO | Diário Solo",
        description=(
            "**Inscrição:** R\$ 4,00\n"
            "**Kill:** +R\$ 2,00\n"
            "**Booyah:** R\$ 40,00 + kills\n\n"
            "⚠️ **Apenas Full Mobile.**\n"
            "*Mobilador e emulador são proibidos.*\n\n"
            "Clique no menu abaixo para selecionar seu horário e fazer sua inscrição automática!"
        ),
        color=0xffd700
    )
    await ctx.send(embed=embed, view=VisualizacaoMenu())

@bot.command()
@commands.has_permissions(administrator=True)
async def definir_sala(ctx, horario: str, *, dados_da_sala: str):
    """Comando para o ADM cadastrar os dados da sala. Ex: !definir_sala 13:00 ID 44552 Senha 12"""
    if horario in salas_cadastradas:
        salas_cadastradas[horario] = dados_da_sala
        await ctx.send(f"✅ Dados da sala das **{horario}** salvos com sucesso!", delete_after=5)
    else:
        await ctx.send("❌ Horário inválido. Use o formato padrão, ex: `13:00`", delete_after=5)

# Alertas automáticos baseados no Horário de Brasília
@tasks.loop(minutes=1)
async def verificar_cronometro():
    agora = datetime.datetime.now()
    horario_atual_str = agora.strftime("%H:%M")
    
    # Calcular os horários alvo de 30 e 10 minutos à frente
    tempo_30m = (agora + datetime.timedelta(minutes=30)).strftime("%H:%M")
    tempo_10m = (agora + datetime.timedelta(minutes=10)).strftime("%H:%M")
    
    # 1. Alerta de 30 minutos antes (Aviso Geral)
    if tempo_30m in inscritos_por_horario:
        jogadores = inscritos_por_horario[tempo_30m]
        for user_id in jogadores.keys():
            try:
                user = await bot.fetch_user(user_id)
                await user.send(f"⚠️ **Aviso da Liga Diário!** Sua sala das **{tempo_30m}** começará em 30 minutos. Fique atento!")
            except:
                pass # Caso a DM do usuário seja fechada

    # 2. Alerta de 10 minutos antes (Entrega de ID e Senha)
    if tempo_10m in inscritos_por_horario:
        jogadores = inscritos_por_horario[tempo_10m]
        info_sala = salas_cadastradas.get(tempo_10m)
        
        for user_id in jogadores.keys():
            try:
                user = await bot.fetch_user(user_id)
                if info_sala:
                    await user.send(f"🔑 **Sua sala das {tempo_10m} vai começar!**\nAqui estão as credenciais de acesso:\n\n{info_sala}")
                else:
                    await user.send(f"⚠️ **Aviso:** Sua sala das **{tempo_10m}** começa em 10 minutos, mas o ADM ainda não liberou os dados de ID/Senha.")
            except:
                pass

bot.run(TOKEN)
                       
