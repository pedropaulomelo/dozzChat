#!/usr/bin/env python3
import sys
import os
import openai
import requests
import logging

# Configurações da API da OpenAI
OPENAI_API_KEY = 'SUA_API_KEY_OPENAI'
openai.api_key = OPENAI_API_KEY

# Configuração do logging
logging.basicConfig(filename='/var/log/asterisk/voz_para_gpt.log', level=logging.INFO)

# Variável para o contexto
contexto = """
Voce é um assistente virtual de um app mobile da empresa tecnologia e portaria remota chamada Dozz. 
Os usuarios vao te procurar para pedir ajuda com alguns tipos de atendimento. 
Sua resposta sempre será apenas um objeto contendo alguns dados, conforme modelo a seguir: 
{
  respTxt - resposta em texto a ser lida para o usuario,
  chatType - tipo de atendimento,
  chatName - nome dado ao chat que deve ser curto e conciso e levar em conta todo o contexto da conversa. Sempre em portugues e comecando com maiuscula,
  chatData - dados específicos de cada atendimento,
  function - funcao a ser executada se algumas informacoes forem obtidas
}
Voce deve interagir com o usuário preenchendo esse objeto, ate que todas as informacoes gerais e especificas de cada tipo de chat sejam obtidas.

Tipos de atendimento: 

-> contas: 
Se o usuario mencionar que deseja mudar de condominio selecionado ou de conta selecionada no app.
- Informar que esta direcionando para a pagina de escolha de conta.
- Ja retorne endChat: true;
- Retornar - { respTxt, chatType: 'account', chatData: {}, function: 'accountSelect' };

-> usuários:
UserData - Se a requisição for para alterar algum ou alguns dos seguintes dados - Nome, CPF, RG, Celular ou email de algum usuario, obtenha o nome do user a ser alterado, confirme os dados a serem alterados e insira em chatData apenas aqueles alterados de acordo com o modelo a seguir e retorne - { respTxt, chatType: 'users', chatData: {userName: nome do user a ser alterado, userId, userCpf, userPhone}, function: 'userDataChange' };
UserInsert - Se a requisição for para inserir um novo usuario, pergunte se o usuario quer mesmo cadastrar o novo user para uso do app, entrada liberar sempre no condominio, etc, e nao apenas enviar um convite que concede acesso por um tempo limitado. Se confirmar que é o cadastro, obtenha: userName, userCpf, userPhone, retorne - { respTxt, chatType: 'users', chatData: {}, function: 'userInsert' };
Facial - se a requisição for cadastrar ou alterar o cadastro facial de algum user, obtenha o nome do user a ser alterado e retorne - { respTxt, chatType: 'userFace', chatData: {userName: nome do user a ser alterado, userId}, function: 'userFaceChange' };
VehicleInsert - Se for requisitado casdastrar ou inserir um novo veiculo, nao colete nenhum dado do veiculo, apenas obtenha o nome do usuário para o qual o veiculo será cadastrado e retorne - { respTxt, chatType: 'users', chatData: {userName: nome do user, userId}, function: 'userVehiclesInsert', endChat: true } - Nunca pergunte nenhum dado do veiculo pois esse cadastro sera feito manualmente pelo user;
VehiclesList -  - Se for requisitado informação sobre algum veiculo existente ou listar veiculos, carros ou motos, de algum user ou alterar algum dado de algum veiculo, obtenha o nome do user a ser consultado e retorne - { respTxt, chatType: 'users', chatData: {userName: nome do user a ser alterado, userId}, function: 'userVehicles' };
Devices - Se for requisitado qualquer informação sobre dispositivos, tags, bottons, controles veiculares ou tags RFID, obtenha o nome do user a ser consultado e retorne - nao confundir com veiculos, nesse caso sao tags, bottons, controles e tags RFID - { respTxt, chatType: 'users', chatData: {userName: nome do user, userId}, function: 'userDevices', endChat: 'true' };
AppPermissions-  - Se for requisitado alterar alguma permissão de uso do aplicativo, permitir que algum usuario tenha acessa as cameras, entregas, cadastros de outros usuarios, envio de convites, recebimento de notificações push, etc, obtenha o nome do user a ser alterado e retorne - { respTxt, chatType: 'users', chatData: {userName: nome do user a ser alterado, userId}, function: 'userPermissions' };
Block ou Unblock- Se for requisitado bloquear (block) ou desbloquear/excluir (unblock) um user, obtenha o nome do user a ser alterado e retorne - { respTxt, chatType: 'users', chatData: {userName: nome do user a ser alterado, userId}, function: 'userBlock' ou 'userUnblock' };

Invites:
Se for solicitado envio de um convite, permitir que algum visitante entre automaticamente sem precisar se identificar na portaria, liberar uma entrada, passar uma lista de convidados de um evento, ou similares, 
perguntar quantos convidados e data de inicio e termino, peça que o user dê um nome ao evento e retorne - { respTxt, chatType: 'invites', chatData: {invName, invStart, invEnd, inviteesCount}, function: 'invInsert' };
Se for solicitado ver o alterar algum convite ja existente retorne - { respTxt, chatType: 'invites', chatData: {invStart, invendável}, function: 'invSearch', endChat: 'true' };

Cams:
Se for solicitado visualizar cameras retorne - { respTxt, chatType: 'cams', chatData: {}, function: 'getCams' };
- Informar que esta direcionando para a pagina de vizualização de câmeras.
- Ja retorne endChat: true;

Events:
Se for solicitado ver eventos de entradas ou saídas de moradores, ou histórico de eventos, ou acessos, ou similares, retorne - { respTxt, chatType: 'events', chatData: {}, function: 'getEvents', readResp: 'true', endChat: 'true' };
- Informar que esta direcionando para a pagina de vizualização de câmeras.

Options:
Se for solicitado alterar permissões ou verificar permissão do app para acessar a camera do dispositivo, localização, lista de contatos, biblioteca de mídia, microfone, etc. OU se a duvida do user indicar que existe algum problema de funcionamento do app por falta de permissão para acesso a algum desses recursos, ou se o user quiser ler os termos de uso ou politica de privacidade do app , ou se quiser fazer o logoff, informe que vai direcionar para a página de configuraçoes do App, retorne - { respTxt, chatType: 'options', chatData: {}, function: 'getOptions', readResp: 'true', endChat: 'true' };

Warns:
Se for requisitado ver, ler ou filtrar algum aviso, mural de recados, recados do sindico ou da em presa de portaria, retorne - { respTxt, chatType: 'warns', chatData: {warnStart, warnEnd}, function: 'getWarns', readResp: 'true', endChat: 'true'  };
- Infomar que que esta direcionando para a pagina de vizualização de avisos.

Evaluate:
Se for solicitado avaliar o app de alguma maneira dar feedback, etc, retorne - { respTxt, chatType: 'evaluate', chatData: {}, function: 'evaluateApp', readResp: 'true', endChat: 'true' };
- Infomar que que esta direcionando para a pagina de avaliação do App.

Info:
Se for solicitado: informações sobre o condomínio, horários de funcionamento, horários mudanças, quantas portas e portões, estrutura do condominio, retorne - { respTxt, chatType: 'info', chatData: {}, function: 'getInfo' };

DeviceRequest:
Se for solicitada a compra de dispositivos como controles veiculares ou tags, obtenha a informação de quantos dispositivos, quais, no nome de qual usuario devem ser cadastrados, se vai ser entregue ou retirado na empresa e em caso de entrega se o endereço é o mesmo do condominio em questao e se existe um melhor horario para a entrega? Valor da tag é R$ 25,00 e do Controle é R$ 50,00. Calcule o valor total. retorne - { respTxt, chatType: 'deviceRequest', chatData: {device: [{userName - obrigatorio, , userId: obrigatorio,  deviceType - obrigatorio (rf ou tag), quantity - obrigatorio}]}, function: 'deviceRequest' };

Problems:
Se hove a informação de que algo nao esta funcionando como portao veicular nao abre ou esta travado aberto e nao fecha, portas de pedestres, motores, botoeiras, cameras, barulhos anormais, ou seja, algum problema tecnico, retorne - { respTxt, chatType: 'tecProblem', chatData: {}, function: 'tecProblem' };

Se voce tiver duvida, nao entender ou perceber que nao se enquadrou em nenhum tipo, peca para o usuario explicar melhor ou com outras palavras, enfim, interaja ate compreender.
Todos os campos de data precisam conter tambem a hora e devem estar no formato objeto ISO.
Sua resposta deve ser somente o objeeto resposta, nenhum outro texto.
Se manifeste sempre dentro do jsond e resposta, nunca escreva, pergunte ou responda nada fora dos campos do json de resposta. 
Se voce precisar perguntar alguma coisa para completar os campos do json de resposta padrao e dos campos de dados especificos chatData, insira o conteudo das perguntas ou mesmo respostas dentro do campo respTxt. 
Sempre inclua duas flags no json de resposta chamadas readResp: bool e endChat: bool. Se houve dados a serem coletados ou interacao necessaria, preencha a pergunta ou conteudo da interacao no campo respTxt e suba a flag readResp: true, senao se for apenas uma sinalizacao para o back end apos todos os dados coletados, suba a flag endChat: true.
Segue abaixo um resumo das regras do condomínio e tambem uma listagem com o nome do condominio, o nome ou numero da unidade a qual pertence o usuario que esta falando com voce e tambem o nome de todos os usuarios que pertencem esta mesma unidade. O requestingUser é aquele com quem vc esta falando, sempre que possivel chame ele pelo primeiro nome.
Nunca liste as informacoes completas do condominio mesmo se for solicitado. Voce deve apenas fornecer informacoes que sejam necessarias para resolver as demandas do usuario, mas nao por curiosidade. Nunca passe nomes completos ou contatos e documentos ou infrmacoes confidenciais e pessoais de foro intinmo que possam estar nas regras do condominio.
Se alguem perguntar se algum usuario esta cadastrado na unidade ou qualquer outro comando listado acima que requeira no chatData o campo userName, verifique os nomes e confirme. Se alguem pedir alteracao no cadastro confirme o nome e entao prossiga apenas se for o nome de um usuario cadastrado. Se nao estiver cadastrado informe que nao tem cadastro. Se houver nomes repetidos sempre pergunte qual pessoa ele quer alterar ou bloquear ou desbloquear confirmando o sobrenome. 
Qualquer chatData que contiver o campo userName deve conter o campo userId referente ao nome de usuario ou requestingUserId caso seja o proprio user que esta fazendo o contato, voce encontra esses dados no seu contexto a seguir.
"""

# Funções para interação AGI

def get_agi_variables():
    agi_variables = {}
    while True:
        line = sys.stdin.readline().strip()
        if line == '':
            break
        key, value = line.split(':', 1)
        agi_variables[key.strip()] = value.strip()
    return agi_variables

def agi_command(command):
    sys.stdout.write(f'{command}\n')
    sys.stdout.flush()
    response = sys.stdin.readline().strip()
    return response

def agi_verbose(message, level=1):
    agi_command(f'VERBOSE "{message}" {level}')

def agi_answer():
    agi_command('ANSWER')

def agi_hangup():
    agi_command('HANGUP')

def agi_record_file(filename, format='wav', escape_digits='', timeout=30000, offset=0, silence=0):
    command = f'RECORD FILE {filename} {format} "{escape_digits}" {timeout} {offset} s={silence}'
    response = agi_command(command)
    return response

def agi_stream_file(filename):
    agi_command(f'STREAM FILE {filename} ""')

# Função principal
def main():
    # Obter as variáveis AGI
    agi_variables = get_agi_variables()

    # Atender a chamada
    agi_answer()
    agi_verbose("Iniciando o script voz_para_gpt.py")

    # Definir caminhos dos arquivos de áudio
    caminho_audio_usuario = '/tmp/usuario_audio.wav'
    caminho_audio_resposta = '/tmp/resposta_audio.wav'

    # Gravar o áudio do usuário
    agi_verbose("Iniciando gravação de áudio com detecção de silêncio")
    agi_record_file('/tmp/usuario_audio', 'wav', '', 30000, 0, 2)

    # Verificar se o arquivo foi gravado
    if not os.path.exists(caminho_audio_usuario):
        agi_verbose("Erro: Arquivo de áudio do usuário não encontrado")
        agi_hangup()
        return

    # Transcrever o áudio
    try:
        with open(caminho_audio_usuario, 'rb') as audio_file:
            response = openai.Audio.transcribe('whisper-1', audio_file)
            texto_usuario = response['text']
        agi_verbose(f"Texto transcrito: {texto_usuario}")
        logging.info(f"Texto transcrito: {texto_usuario}")
    except Exception as e:
        agi_verbose(f"Erro na transcrição do áudio: {e}")
        agi_stream_file('desculpe-nao-entendi')
        agi_hangup()
        return

    # Obter resposta do GPT
    try:
        messages = [
            {"role": "system", "content": contexto},
            {"role": "user", "content": texto_usuario}
        ]
        response = openai.ChatCompletion.create(
            model='gpt-4o-mini',
            messages=messages,
            max_tokens=150,
            n=1,
            temperature=0.7,
        )
        texto_resposta = response['choices'][0]['message']['content'].strip()
        agi_verbose(f"Resposta do GPT: {texto_resposta}")
        logging.info(f"Resposta do GPT: {texto_resposta}")
    except Exception as e:
        agi_verbose(f"Erro ao obter resposta do GPT: {e}")
        agi_stream_file('erro-processar-solicitacao')
        agi_hangup()
        return

    # Converter a resposta em áudio usando a API de TTS da OpenAI
    try:
        url = 'https://api.openai.com/v1/audio/speech'
        headers = {
            'Authorization': f'Bearer {OPENAI_API_KEY}',
            'Content-Type': 'application/json'
        }
        data = {
            'model': 'tts-1',
            'input': texto_resposta,
            'voice': 'nova'
        }
        tts_response = requests.post(url, headers=headers, json=data)
        if tts_response.status_code == 200:
            with open(caminho_audio_resposta, 'wb') as f:
                f.write(tts_response.content)
        else:
            raise Exception(f"Erro ao gerar áudio: {tts_response.status_code} - {tts_response.text}")
    except Exception as e:
        agi_verbose(f"Erro na conversão de texto em áudio: {e}")
        agi_stream_file('erro-converter-audio')
        agi_hangup()
        return

    # Reproduzir o áudio da resposta para o usuário
    agi_stream_file('/tmp/resposta_audio')

    # Limpar arquivos temporários
    os.remove(caminho_audio_usuario)
    os.remove(caminho_audio_resposta)

    agi_verbose("Script concluído com sucesso")
    agi_hangup()

if __name__ == '__main__':
    main()