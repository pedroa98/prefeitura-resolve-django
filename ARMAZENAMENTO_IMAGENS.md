# Armazenamento de imagens no Supabase Storage

O campo de imagem das solicitações usa o armazenamento local quando as variáveis S3 não estão definidas. Com as cinco variáveis abaixo configuradas, o Django grava os arquivos no bucket Supabase por meio do protocolo S3. O bucket deve permanecer privado; a aplicação já verifica a autorização antes de abrir a imagem.

## Supabase

1. Em **Storage**, crie um bucket privado chamado `solicitacoes` (ou use outro nome e atualize `SUPABASE_S3_BUCKET`).
2. Em **Storage → Configuration → S3**, habilite a conexão S3 e gere um novo par de chaves.
3. Use o endpoint e a região exibidos para o projeto. Neste projeto, os valores esperados são o endpoint `https://lznkytdjzbcqmiwwbxrc.storage.supabase.co/storage/v1/s3` e a região `ca-central-1`.
4. Não reutilize chaves que tenham sido compartilhadas em mensagens ou commits. Revogue-as e gere outras. As chaves S3 são credenciais de servidor e não devem ir para o GitHub, para o navegador ou para arquivos versionados.

## Execução local no PowerShell

1. Atualize o clone para a branch com esta configuração.
2. Instale as dependências: `python -m pip install -r requirements.txt`.
3. Copie o modelo e edite o arquivo local:
   ```powershell
   Copy-Item .env.example .env
   notepad .env
   ```
4. Preencha `SUPABASE_S3_ACCESS_KEY_ID` e `SUPABASE_S3_SECRET_ACCESS_KEY` no arquivo `.env` com o par recém-gerado. O `.env` está ignorado pelo Git. Não cole os valores em chats ou commits.
5. Confirme a configuração e inicie:
   ```powershell
   python manage.py check
   python manage.py runserver
   ```

Quando todas as variáveis estiverem definidas, o Django seleciona o backend S3. Se apenas parte delas estiver preenchida, o Django interrompe a inicialização com uma mensagem de configuração, em vez de tentar usar credenciais incompletas. Se nenhuma estiver configurada, o desenvolvimento local continua usando o armazenamento de arquivos local.

## Vercel

Em **Project → Settings → Environment Variables**, habilite **Automatically expose System Environment Variables**. O Django usa `VERCEL_URL`, `VERCEL_BRANCH_URL` e `VERCEL_PROJECT_PRODUCTION_URL` para aceitar os domínios de deploy e preview do próprio projeto. Crie também estas variáveis para **Production** (e **Preview**, se for testar previews):

- `SUPABASE_S3_ENDPOINT`
- `SUPABASE_S3_REGION`
- `SUPABASE_S3_BUCKET`
- `SUPABASE_S3_ACCESS_KEY_ID`
- `SUPABASE_S3_SECRET_ACCESS_KEY`

Use os mesmos valores do painel S3 do Supabase; marque as duas chaves como sensíveis quando a interface permitir. Depois, faça um novo deploy. Variáveis de ambiente não devem ser colocadas no código nem no repositório.

## Teste funcional

1. Envie uma solicitação anônima com imagem e confirme que o registro é criado e o arquivo aparece no bucket.
2. Acesse a solicitação com protocolo e chave e confirme que a imagem pode ser aberta.
3. Entre com uma conta e repita o envio; confirme que a solicitação e a imagem ficam acessíveis à conta autorizada.
4. Tente acessar a imagem sem autorização; a aplicação deve responder como recurso não encontrado.

Não há alteração de modelos nem migração de banco de dados: o banco continua guardando o caminho do arquivo, e os bytes da imagem ficam no Storage.
