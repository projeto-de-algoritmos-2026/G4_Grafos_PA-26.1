async function buscar() {
    const origem = document.getElementById('origem').value;
    const destino = document.getElementById('destino').value;
    const divResultados = document.getElementById('resultados');

    if (!origem || !destino) {
        alert("Por favor, preencha origem e destino.");
        return;
    }

    divResultados.style.display = 'block';
    divResultados.style.color = '#555';
    divResultados.textContent = "Buscando as melhores opções...";

    try {
        const response = await fetch(`/api/rotas?origem=${origem}&destino=${destino}`);
        const data = await response.json();

        divResultados.style.color = '#333';
        if (response.ok) {
            divResultados.textContent = JSON.stringify(data, null, 4);
        } else {
            divResultados.textContent = "Erro: " + (data.erro || "Falha na busca.");
        }
    } catch (error) {
        divResultados.style.color = '#d32f2f';
        divResultados.textContent = "Erro de conexão com o servidor:\n" + error;
    }
}