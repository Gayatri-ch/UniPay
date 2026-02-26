let walletBalance = 1000;
const walletEl = document.getElementById('walletBalance');
const historyTable = document.getElementById('historyTable');

function updateBalance(amount) {
    walletBalance -= amount;
    if(walletEl) walletEl.textContent = walletBalance.toFixed(2);
}

function addHistory(receiver, amount, status) {
    if(!historyTable) return;
    const row = document.createElement('tr');
    row.innerHTML = `<td>${receiver}</td><td>$${amount.toFixed(2)}</td><td class='${status === 'Success' ? 'success' : 'danger'}'>${status}</td>`;
    historyTable.appendChild(row);
}

function simulatePayment(receiver) {
    const amount = parseFloat(prompt(`Enter amount to send to ${receiver}:`, '0'));
    if(isNaN(amount) || amount <= 0){
        alert('Invalid amount.');
        return;
    }
    if(amount > walletBalance){
        alert('Insufficient balance!');
        addHistory(receiver, amount, 'Failed');
        return;
    }
    updateBalance(amount);
    addHistory(receiver, amount, 'Success');
    alert(`$${amount.toFixed(2)} sent to ${receiver} (simulated).`);
}
