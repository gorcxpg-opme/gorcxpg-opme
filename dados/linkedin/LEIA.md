# Certificados do LinkedIn (opcional)

Se você baixar a cópia dos seus dados do LinkedIn (Configurações e privacidade → Privacidade de dados → Obter uma cópia dos seus dados) e o pacote trouxer um arquivo `Certifications.csv`, coloque esse arquivo aqui, nesta pasta, com esse mesmo nome.

O script junta esses certificados aos de `dados/certificados.csv`, sem repetir os que já estão lá, e tenta adivinhar a área pelo nome do curso. Horas não vêm do LinkedIn; se quiser que entrem na conta, copie a linha para `dados/certificados.csv` e preencha a coluna `horas`.
