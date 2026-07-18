import streamlit as st

COPAS = {
    "2026 🇺🇸🇲🇽🇨🇦": {
        "resultado": "Oitavas de final",
        "tecnico": "Carlo Ancelotti",
        "jogadores": [
            {"nome": "Alisson", "posicao": "Goleiro", "clube": "Liverpool"},
            {"nome": "Ederson", "posicao": "Goleiro", "clube": "Fenerbahçe"},
            {"nome": "Weverton", "posicao": "Goleiro", "clube": "Grêmio"},
            {"nome": "Marquinhos", "posicao": "Zagueiro", "clube": "PSG"},
            {"nome": "Gabriel Magalhães", "posicao": "Zagueiro", "clube": "Arsenal"},
            {"nome": "Bremer", "posicao": "Zagueiro", "clube": "Juventus"},
            {"nome": "Léo Pereira", "posicao": "Zagueiro", "clube": "Flamengo"},
            {"nome": "Roger Ibañez", "posicao": "Zagueiro", "clube": "Al-Ahli"},
            {"nome": "Danilo", "posicao": "Lateral", "clube": "Flamengo"},
            {"nome": "Alex Sandro", "posicao": "Lateral", "clube": "Flamengo"},
            {"nome": "Douglas Santos", "posicao": "Lateral", "clube": "Zenit"},
            {"nome": "Casemiro", "posicao": "Volante", "clube": "Manchester United"},
            {"nome": "Bruno Guimarães", "posicao": "Volante", "clube": "Newcastle"},
            {"nome": "Fabinho", "posicao": "Volante", "clube": "Al-Ittihad"},
            {"nome": "Éderson Silva", "posicao": "Volante", "clube": "Atalanta"},
            {"nome": "Danilo Santos", "posicao": "Volante", "clube": "Botafogo"},
            {"nome": "Lucas Paquetá", "posicao": "Meia", "clube": "Flamengo"},
            {"nome": "Neymar", "posicao": "Atacante", "clube": "Santos"},
            {"nome": "Vinícius Júnior", "posicao": "Atacante", "clube": "Real Madrid"},
            {"nome": "Raphinha", "posicao": "Atacante", "clube": "Barcelona"},
            {"nome": "Matheus Cunha", "posicao": "Atacante", "clube": "Manchester United"},
            {"nome": "Gabriel Martinelli", "posicao": "Atacante", "clube": "Arsenal"},
            {"nome": "Luiz Henrique", "posicao": "Atacante", "clube": "Zenit"},
            {"nome": "Endrick", "posicao": "Atacante", "clube": "Lyon"},
            {"nome": "Igor Thiago", "posicao": "Atacante", "clube": "Brentford"},
            {"nome": "Rayan", "posicao": "Atacante", "clube": "Bournemouth"},
        ],
    },
    "2022 🇶🇦": {
        "resultado": "Quartas de final",
        "tecnico": "Tite",
        "jogadores": [
            {"nome": "Alisson", "posicao": "Goleiro", "clube": "Liverpool"},
            {"nome": "Ederson", "posicao": "Goleiro", "clube": "Manchester City"},
            {"nome": "Weverton", "posicao": "Goleiro", "clube": "Palmeiras"},
            {"nome": "Danilo", "posicao": "Lateral Direito", "clube": "Juventus"},
            {"nome": "Daniel Alves", "posicao": "Lateral Direito", "clube": "Pumas"},
            {"nome": "Alex Sandro", "posicao": "Lateral Esquerdo", "clube": "Juventus"},
            {"nome": "Alex Telles", "posicao": "Lateral Esquerdo", "clube": "Sevilla"},
            {"nome": "Marquinhos", "posicao": "Zagueiro", "clube": "PSG"},
            {"nome": "Thiago Silva", "posicao": "Zagueiro", "clube": "Chelsea"},
            {"nome": "Éder Militão", "posicao": "Zagueiro", "clube": "Real Madrid"},
            {"nome": "Bremer", "posicao": "Zagueiro", "clube": "Juventus"},
            {"nome": "Casemiro", "posicao": "Volante", "clube": "Manchester United"},
            {"nome": "Fred (Volante)", "posicao": "Volante", "clube": "Manchester United"},
            {"nome": "Fabinho", "posicao": "Volante", "clube": "Liverpool"},
            {"nome": "Bruno Guimarães", "posicao": "Volante", "clube": "Newcastle"},
            {"nome": "Lucas Paquetá", "posicao": "Meia", "clube": "West Ham"},
            {"nome": "Éverton Ribeiro", "posicao": "Meia", "clube": "Flamengo"},
            {"nome": "Neymar", "posicao": "Atacante", "clube": "PSG"},
            {"nome": "Raphinha", "posicao": "Atacante", "clube": "Barcelona"},
            {"nome": "Vini Jr.", "posicao": "Atacante", "clube": "Real Madrid"},
            {"nome": "Rodrygo", "posicao": "Atacante", "clube": "Real Madrid"},
            {"nome": "Antony", "posicao": "Atacante", "clube": "Manchester United"},
            {"nome": "Gabriel Martinelli", "posicao": "Atacante", "clube": "Arsenal"},
            {"nome": "Richarlison", "posicao": "Atacante", "clube": "Tottenham"},
            {"nome": "Gabriel Jesus", "posicao": "Atacante", "clube": "Arsenal"},
            {"nome": "Pedro", "posicao": "Atacante", "clube": "Flamengo"},
        ],
    },
    "2018 🇷🇺": {
        "resultado": "Quartas de final",
        "tecnico": "Tite",
        "jogadores": [
            {"nome": "Alisson", "posicao": "Goleiro", "clube": "Liverpool"},
            {"nome": "Ederson", "posicao": "Goleiro", "clube": "Manchester City"},
            {"nome": "Cássio", "posicao": "Goleiro", "clube": "Corinthians"},
            {"nome": "Danilo", "posicao": "Lateral Direito", "clube": "Juventus"},
            {"nome": "Fagner", "posicao": "Lateral Direito", "clube": "Corinthians"},
            {"nome": "Marcelo", "posicao": "Lateral Esquerdo", "clube": "Real Madrid"},
            {"nome": "Filipe Luís", "posicao": "Lateral Esquerdo", "clube": "Atlético de Madrid"},
            {"nome": "Thiago Silva", "posicao": "Zagueiro", "clube": "PSG"},
            {"nome": "Miranda", "posicao": "Zagueiro", "clube": "Inter de Milão"},
            {"nome": "Marquinhos", "posicao": "Zagueiro", "clube": "PSG"},
            {"nome": "Pedro Geromel", "posicao": "Zagueiro", "clube": "Grêmio"},
            {"nome": "Casemiro", "posicao": "Volante", "clube": "Real Madrid"},
            {"nome": "Fernandinho", "posicao": "Volante", "clube": "Manchester City"},
            {"nome": "Paulinho", "posicao": "Volante", "clube": "Guangzhou Evergrande"},
            {"nome": "Renato Augusto", "posicao": "Meia", "clube": "Beijing Guoan"},
            {"nome": "Philippe Coutinho", "posicao": "Meia", "clube": "Barcelona"},
            {"nome": "Willian", "posicao": "Meia", "clube": "Chelsea"},
            {"nome": "Fred (Meia)", "posicao": "Meia", "clube": "Shakhtar Donetsk"},
            {"nome": "Neymar", "posicao": "Atacante", "clube": "PSG"},
            {"nome": "Douglas Costa", "posicao": "Atacante", "clube": "Juventus"},
            {"nome": "Taison", "posicao": "Atacante", "clube": "Shakhtar Donetsk"},
            {"nome": "Gabriel Jesus", "posicao": "Atacante", "clube": "Manchester City"},
            {"nome": "Roberto Firmino", "posicao": "Atacante", "clube": "Liverpool"},
        ],
    },
    "2014 🇧🇷": {
        "resultado": "4º lugar",
        "tecnico": "Luiz Felipe Scolari",
        "jogadores": [
            {"nome": "Júlio César", "posicao": "Goleiro", "clube": "Toronto FC"},
            {"nome": "Jefferson", "posicao": "Goleiro", "clube": "Botafogo"},
            {"nome": "Victor", "posicao": "Goleiro", "clube": "Atlético-MG"},
            {"nome": "Maicon", "posicao": "Lateral Direito", "clube": "Roma"},
            {"nome": "Daniel Alves", "posicao": "Lateral Direito", "clube": "Barcelona"},
            {"nome": "Marcelo", "posicao": "Lateral Esquerdo", "clube": "Real Madrid"},
            {"nome": "Maxwell", "posicao": "Lateral Esquerdo", "clube": "PSG"},
            {"nome": "Thiago Silva", "posicao": "Zagueiro", "clube": "PSG"},
            {"nome": "David Luiz", "posicao": "Zagueiro", "clube": "Chelsea"},
            {"nome": "Dante", "posicao": "Zagueiro", "clube": "Bayern de Munique"},
            {"nome": "Henrique", "posicao": "Zagueiro", "clube": "Napoli"},
            {"nome": "Luiz Gustavo", "posicao": "Volante", "clube": "Wolfsburg"},
            {"nome": "Fernandinho", "posicao": "Volante", "clube": "Manchester City"},
            {"nome": "Paulinho", "posicao": "Meia", "clube": "Tottenham"},
            {"nome": "Oscar", "posicao": "Meia", "clube": "Chelsea"},
            {"nome": "Willian", "posicao": "Meia", "clube": "Chelsea"},
            {"nome": "Ramires", "posicao": "Meia", "clube": "Chelsea"},
            {"nome": "Hernanes", "posicao": "Meia", "clube": "Inter de Milão"},
            {"nome": "Neymar", "posicao": "Atacante", "clube": "Barcelona"},
            {"nome": "Hulk", "posicao": "Atacante", "clube": "Zenit"},
            {"nome": "Bernard", "posicao": "Atacante", "clube": "Shakhtar Donetsk"},
            {"nome": "Fred (Atacante)", "posicao": "Atacante", "clube": "Fluminense"},
            {"nome": "Jô", "posicao": "Atacante", "clube": "Atlético-MG"},
        ],
    },
    "2010 🇿🇦": {
        "resultado": "Quartas de final",
        "tecnico": "Dunga",
        "jogadores": [
            {"nome": "Júlio César", "posicao": "Goleiro", "clube": "Inter de Milão"},
            {"nome": "Gomes", "posicao": "Goleiro", "clube": "Tottenham"},
            {"nome": "Doni", "posicao": "Goleiro", "clube": "Roma"},
            {"nome": "Maicon", "posicao": "Lateral Direito", "clube": "Inter de Milão"},
            {"nome": "Daniel Alves", "posicao": "Lateral Direito", "clube": "Barcelona"},
            {"nome": "Michel Bastos", "posicao": "Lateral Esquerdo", "clube": "Lyon"},
            {"nome": "Gilberto", "posicao": "Lateral Esquerdo", "clube": "Cruzeiro"},
            {"nome": "Lúcio", "posicao": "Zagueiro", "clube": "Inter de Milão"},
            {"nome": "Juan", "posicao": "Zagueiro", "clube": "Roma"},
            {"nome": "Thiago Silva", "posicao": "Zagueiro", "clube": "Milan"},
            {"nome": "Luisão", "posicao": "Zagueiro", "clube": "Benfica"},
            {"nome": "Gilberto Silva", "posicao": "Volante", "clube": "Panathinaikos"},
            {"nome": "Felipe Melo", "posicao": "Volante", "clube": "Juventus"},
            {"nome": "Josué", "posicao": "Volante", "clube": "Wolfsburg"},
            {"nome": "Kleberson", "posicao": "Meia", "clube": "Flamengo"},
            {"nome": "Kaká", "posicao": "Meia", "clube": "Real Madrid"},
            {"nome": "Ramires", "posicao": "Meia", "clube": "Benfica"},
            {"nome": "Elano", "posicao": "Meia", "clube": "Galatasaray"},
            {"nome": "Júlio Baptista", "posicao": "Atacante", "clube": "Roma"},
            {"nome": "Robinho", "posicao": "Atacante", "clube": "Santos"},
            {"nome": "Luís Fabiano", "posicao": "Atacante", "clube": "Sevilla"},
            {"nome": "Nilmar", "posicao": "Atacante", "clube": "Villarreal"},
            {"nome": "Grafite", "posicao": "Atacante", "clube": "Wolfsburg"},
        ],
    },
    "2006 🇩🇪": {
        "resultado": "Quartas de final",
        "tecnico": "Carlos Alberto Parreira",
        "jogadores": [
            {"nome": "Dida", "posicao": "Goleiro", "clube": "Milan"},
            {"nome": "Rogério Ceni", "posicao": "Goleiro", "clube": "São Paulo"},
            {"nome": "Júlio César", "posicao": "Goleiro", "clube": "Inter de Milão"},
            {"nome": "Cafu", "posicao": "Lateral Direito", "clube": "Milan"},
            {"nome": "Cícinho", "posicao": "Lateral Direito", "clube": "Real Madrid"},
            {"nome": "Roberto Carlos", "posicao": "Lateral Esquerdo", "clube": "Real Madrid"},
            {"nome": "Gilberto", "posicao": "Lateral Esquerdo", "clube": "Hertha Berlim"},
            {"nome": "Lúcio", "posicao": "Zagueiro", "clube": "Bayern de Munique"},
            {"nome": "Cris", "posicao": "Zagueiro", "clube": "Lyon"},
            {"nome": "Juan", "posicao": "Zagueiro", "clube": "Bayer Leverkusen"},
            {"nome": "Luisão", "posicao": "Zagueiro", "clube": "Benfica"},
            {"nome": "Emerson", "posicao": "Volante", "clube": "Juventus"},
            {"nome": "Gilberto Silva", "posicao": "Volante", "clube": "Arsenal"},
            {"nome": "Zé Roberto", "posicao": "Meia", "clube": "Bayern de Munique"},
            {"nome": "Juninho Pernambucano", "posicao": "Meia", "clube": "Lyon"},
            {"nome": "Kaká", "posicao": "Meia", "clube": "Milan"},
            {"nome": "Ronaldinho", "posicao": "Meia", "clube": "Barcelona"},
            {"nome": "Mineiro", "posicao": "Meia", "clube": "São Paulo"},
            {"nome": "Ricardinho", "posicao": "Meia", "clube": "Corinthians"},
            {"nome": "Robinho", "posicao": "Atacante", "clube": "Real Madrid"},
            {"nome": "Adriano", "posicao": "Atacante", "clube": "Inter de Milão"},
            {"nome": "Ronaldo", "posicao": "Atacante", "clube": "Real Madrid"},
            {"nome": "Fred (Atacante)", "posicao": "Atacante", "clube": "Lyon"},
        ],
    },
    "2002 🇰🇷🇯🇵": {
        "resultado": "🏆 Campeão",
        "tecnico": "Luiz Felipe Scolari",
        "jogadores": [
            {"nome": "Marcos", "posicao": "Goleiro", "clube": "Palmeiras"},
            {"nome": "Rogério Ceni", "posicao": "Goleiro", "clube": "São Paulo"},
            {"nome": "Dida", "posicao": "Goleiro", "clube": "Corinthians"},
            {"nome": "Cafu", "posicao": "Lateral Direito", "clube": "Roma"},
            {"nome": "Belletti", "posicao": "Lateral Direito", "clube": "São Paulo"},
            {"nome": "Roberto Carlos", "posicao": "Lateral Esquerdo", "clube": "Real Madrid"},
            {"nome": "Júnior", "posicao": "Lateral Esquerdo", "clube": "Parma"},
            {"nome": "Lúcio", "posicao": "Zagueiro", "clube": "Bayer Leverkusen"},
            {"nome": "Edmílson", "posicao": "Zagueiro", "clube": "Lyon"},
            {"nome": "Roque Júnior", "posicao": "Zagueiro", "clube": "Milan"},
            {"nome": "Anderson Polga", "posicao": "Zagueiro", "clube": "Grêmio"},
            {"nome": "Gilberto Silva", "posicao": "Volante", "clube": "Atlético-MG"},
            {"nome": "Kléberson", "posicao": "Volante", "clube": "Atlético-PR"},
            {"nome": "Vampeta", "posicao": "Volante", "clube": "Corinthians"},
            {"nome": "Ronaldinho", "posicao": "Meia", "clube": "PSG"},
            {"nome": "Juninho Paulista", "posicao": "Meia", "clube": "Flamengo"},
            {"nome": "Ricardinho", "posicao": "Meia", "clube": "Corinthians"},
            {"nome": "Denílson", "posicao": "Atacante", "clube": "Real Betis"},
            {"nome": "Kaká", "posicao": "Meia", "clube": "São Paulo"},
            {"nome": "Ronaldo", "posicao": "Atacante", "clube": "Inter de Milão"},
            {"nome": "Rivaldo", "posicao": "Atacante", "clube": "Barcelona"},
            {"nome": "Luizão", "posicao": "Atacante", "clube": "Grêmio"},
            {"nome": "Edílson", "posicao": "Atacante", "clube": "Cruzeiro"},
        ],
    },
    "1998 🇫🇷": {
        "resultado": "Vice-campeão",
        "tecnico": "Mário Zagallo",
        "jogadores": [
            {"nome": "Taffarel", "posicao": "Goleiro", "clube": "Atlético-MG"},
            {"nome": "Dida", "posicao": "Goleiro", "clube": "Cruzeiro"},
            {"nome": "Carlos Germano", "posicao": "Goleiro", "clube": "Vasco"},
            {"nome": "Cafu", "posicao": "Lateral Direito", "clube": "Roma"},
            {"nome": "Zé Carlos", "posicao": "Lateral Direito", "clube": "São Paulo"},
            {"nome": "Roberto Carlos", "posicao": "Lateral Esquerdo", "clube": "Real Madrid"},
            {"nome": "Zé Roberto", "posicao": "Lateral Esquerdo", "clube": "Flamengo"},
            {"nome": "Júnior Baiano", "posicao": "Zagueiro", "clube": "Flamengo"},
            {"nome": "Aldair", "posicao": "Zagueiro", "clube": "Roma"},
            {"nome": "Emerson", "posicao": "Volante", "clube": "Bayer Leverkusen"},
            {"nome": "André Cruz", "posicao": "Zagueiro", "clube": "Milan"},
            {"nome": "Gonçalves", "posicao": "Zagueiro", "clube": "Botafogo"},
            {"nome": "César Sampaio", "posicao": "Volante", "clube": "Yokohama Flügels"},
            {"nome": "Dunga", "posicao": "Volante", "clube": "Jubilo Iwata"},
            {"nome": "Leonardo", "posicao": "Meia", "clube": "Milan"},
            {"nome": "Rivaldo", "posicao": "Meia", "clube": "Barcelona"},
            {"nome": "Doriva", "posicao": "Volante", "clube": "Porto"},
            {"nome": "Denílson", "posicao": "Atacante", "clube": "Real Betis"},
            {"nome": "Bebeto", "posicao": "Atacante", "clube": "Botafogo"},
            {"nome": "Ronaldo", "posicao": "Atacante", "clube": "Inter de Milão"},
            {"nome": "Edmundo", "posicao": "Atacante", "clube": "Fiorentina"},
            {"nome": "Giovanni", "posicao": "Atacante", "clube": "Barcelona"},
        ],
    },
    "1994 🇺🇸": {
        "resultado": "🏆 Campeão",
        "tecnico": "Carlos Alberto Parreira",
        "jogadores": [
            {"nome": "Taffarel", "posicao": "Goleiro", "clube": "Reggiana"},
            {"nome": "Zetti", "posicao": "Goleiro", "clube": "São Paulo"},
            {"nome": "Gilmar Rinaldi", "posicao": "Goleiro", "clube": "Flamengo"},
            {"nome": "Jorginho", "posicao": "Lateral Direito", "clube": "Bayern"},
            {"nome": "Cafu", "posicao": "Lateral Direito", "clube": "São Paulo"},
            {"nome": "Branco", "posicao": "Lateral Esquerdo", "clube": "Fluminense"},
            {"nome": "Leonardo", "posicao": "Lateral Esquerdo", "clube": "São Paulo"},
            {"nome": "Aldair", "posicao": "Zagueiro", "clube": "Roma"},
            {"nome": "Ricardo Rocha", "posicao": "Zagueiro", "clube": "Vasco da Gama"},
            {"nome": "Márcio Santos", "posicao": "Zagueiro", "clube": "Bordeaux"},
            {"nome": "Ronaldão", "posicao": "Zagueiro", "clube": "Shimizu S-Pulse"},
            {"nome": "Dunga", "posicao": "Volante", "clube": "Stuttgart"},
            {"nome": "Mauro Silva", "posicao": "Volante", "clube": "Deportivo La Coruña"},
            {"nome": "Mazinho", "posicao": "Volante", "clube": "Palmeiras"},
            {"nome": "Zinho", "posicao": "Meia", "clube": "Palmeiras"},
            {"nome": "Raí", "posicao": "Meia", "clube": "PSG"},
            {"nome": "Paulo Sérgio", "posicao": "Meia", "clube": "Bayer Leverkusen"},
            {"nome": "Bebeto", "posicao": "Atacante", "clube": "Deportivo La Coruña"},
            {"nome": "Romário", "posicao": "Atacante", "clube": "Barcelona"},
            {"nome": "Müller", "posicao": "Atacante", "clube": "São Paulo"},
            {"nome": "Rolando", "posicao": "Atacante", "clube": "Cruzeiro"},
            {"nome": "Viola", "posicao": "Atacante", "clube": "Corinthians"},
        ],
    },
    "1990 🇮🇹": {
        "resultado": "Oitavas de final",
        "tecnico": "Sebastião Lazaroni",
        "jogadores": [
            {"nome": "Taffarel", "posicao": "Goleiro", "clube": "Internacional"},
            {"nome": "Zé Carlos", "posicao": "Goleiro", "clube": "Flamengo"},
            {"nome": "Acácio", "posicao": "Goleiro", "clube": "Vasco da Gama"},
            {"nome": "Jorginho", "posicao": "Lateral Direito", "clube": "Bayer Leverkusen"},
            {"nome": "Mazinho", "posicao": "Lateral Direito", "clube": "Vasco da Gama"},
            {"nome": "Branco", "posicao": "Lateral Esquerdo", "clube": "Porto"},
            {"nome": "Ricardo Gomes", "posicao": "Zagueiro", "clube": "Benfica"},
            {"nome": "Mozer", "posicao": "Zagueiro", "clube": "Marseille"},
            {"nome": "Aldair", "posicao": "Zagueiro", "clube": "Benfica"},
            {"nome": "Ricardo Rocha", "posicao": "Zagueiro", "clube": "São Paulo"},
            {"nome": "Mauro Galvão", "posicao": "Zagueiro", "clube": "Botafogo"},
            {"nome": "Alemão", "posicao": "Volante", "clube": "Napoli"},
            {"nome": "Dunga", "posicao": "Meia", "clube": "Fiorentina"},
            {"nome": "Bismarck", "posicao": "Meia", "clube": "Vasco da Gama"},
            {"nome": "Valdo", "posicao": "Meia", "clube": "Benfica"},
            {"nome": "Tita", "posicao": "Meia", "clube": "Vasco da Gama"},
            {"nome": "Silas", "posicao": "Meia", "clube": "Sporting CP"},
            {"nome": "Careca", "posicao": "Atacante", "clube": "Napoli"},
            {"nome": "Romário", "posicao": "Atacante", "clube": "PSV Eindhoven"},
            {"nome": "Müller", "posicao": "Atacante", "clube": "Torino"},
            {"nome": "Bebeto", "posicao": "Atacante", "clube": "Vasco da Gama"},
            {"nome": "Renato Gaúcho", "posicao": "Atacante", "clube": "Flamengo"},
        ],
    },
}


def render(modo_edicao: bool):
    st.subheader("🇧🇷 Brasil em Copas do Mundo")

    copas_keys = list(COPAS.keys())

    # Seletor de copas
    copas_selecionadas = st.multiselect(
        "Selecione as copas para exibir",
        options=copas_keys,
        default=copas_keys,
        key="copas_filtro",
    )

    copas_filtradas = [c for c in copas_keys if c in copas_selecionadas]

    # Calcular percentuais primeiro para a média
    percentuais = []
    for idx, copa in enumerate(copas_keys):
        if idx < len(copas_keys) - 1:
            nomes_atual = {j["nome"] for j in COPAS[copa]["jogadores"]}
            nomes_anterior = {j["nome"] for j in COPAS[copas_keys[idx + 1]]["jogadores"]}
            remanescentes = nomes_atual & nomes_anterior
            total_anterior = len(nomes_anterior)
            pct = (len(remanescentes) / total_anterior * 100) if total_anterior else 0
            percentuais.append(pct)

    if percentuais:
        media_pct = sum(percentuais) / len(percentuais)
        st.caption(f"Média de remanescentes entre copas: **{media_pct:.0f}%** (de 1994 a 2026)")

    for idx, copa in enumerate(copas_keys):
        if copa not in copas_filtradas:
            continue
        dados = COPAS[copa]
        resultado = dados["resultado"]
        tecnico = dados["tecnico"]
        jogadores = dados["jogadores"]
        nomes_atual = {j["nome"] for j in jogadores}

        # Calcular remanescentes da copa anterior
        remanescentes_info = ""
        remanescentes_nomes = []
        if idx < len(copas_keys) - 1:
            copa_anterior = copas_keys[idx + 1]
            nomes_anterior = {j["nome"] for j in COPAS[copa_anterior]["jogadores"]}
            remanescentes_nomes = sorted(nomes_atual & nomes_anterior)
            qtd = len(remanescentes_nomes)
            total_anterior = len(nomes_anterior)
            pct = (qtd / total_anterior * 100) if total_anterior else 0
            remanescentes_info = f" | {qtd}/{total_anterior} da copa anterior ({pct:.0f}%)"

        with st.expander(f"{copa} — {resultado} ({tecnico}){remanescentes_info}"):
            # Agrupar por posição
            posicoes_ordem = ["Goleiro", "Lateral Direito", "Lateral Esquerdo", "Lateral", "Zagueiro", "Volante", "Meia", "Ponta", "Atacante"]
            for pos in posicoes_ordem:
                jogadores_pos = [j for j in jogadores if j["posicao"] == pos]
                if jogadores_pos:
                    nomes = ", ".join([f"**{j['nome']}** ({j['clube']})" for j in jogadores_pos])
                    st.markdown(f"**{pos}:** {nomes}")

            if remanescentes_nomes:
                st.divider()
                st.caption(f"Remanescentes da copa anterior: {', '.join(remanescentes_nomes)}")
