const stocksDiv = document.getElementById('stocksGrid');

const socket = new WebSocket('ws://localhost:8000/ws/Stocks/');

socket.onmessage = function(event) {
    const data = JSON.parse(event.data);
    if (data.type === 'trade' && data.data) {
        data.data.forEach(trade => {
            const symbol = trade.s;
            const price = trade.p;
            let stockDiv = document.getElementById(`stock-${symbol}`);

            if (!stockDiv) {
                stockDiv = document.createElement('div');
                stockDiv.id = `stock-${symbol}`;
                stockDiv.classList.add('stock');
                stockDiv.innerHTML = `<div class="stock-name">${symbol}</div>
                                      <div class="stock-price" id="price-${symbol}"></div>`;
                stocksDiv.appendChild(stockDiv);
            }

            const priceDiv = document.getElementById(`price-${symbol}`);
            priceDiv.innerHTML = `$${price.toFixed(2)}`;
        });
    }
};
