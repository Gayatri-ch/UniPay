(() => {
  const BANKS = [
    { code: 'SBI', name: 'State Bank of India', img: '../static/images/sbi.png' },
    { code: 'HDFC', name: 'HDFC Bank', img: '../static/images/hdfc.png' },
    { code: 'ICICI', name: 'ICICI Bank', img: '../static/images/icici.png' },
    { code: 'AXIS', name: 'Axis Bank', img: '../static/images/axis.png' },
    { code: 'KOTAK', name: 'Kotak Mahindra Bank', img: '../static/images/kotak.png' },
    { code: 'PAYTM', name: 'Paytm Payments Bank', img: '../static/images/paytm.png' },
    { code: 'PNB', name: 'Punjab National Bank', img: '../static/images/pnb.png' },
    { code: 'UNION', name: 'Union Bank of India', img: '../static/images/union.png' },
    { code: 'BOB', name: 'Bank of Baroda', img: '../static/images/bob.png' },
    { code: 'CAN', name: 'Canara Bank', img: '../static/images/canara.png' },
    { code: 'YES', name: 'Yes Bank', img: '../static/images/yes.png' },
    { code: 'IDFC', name: 'IDFC First Bank', img: '../static/images/idfc.png' }
  ];

  const bankGrid = document.getElementById('bankGrid');

  function renderBanks() {
    bankGrid.innerHTML = '';
    BANKS.forEach(bank => {
      const div = document.createElement('div');
      div.className = 'bank-card';
      div.innerHTML = `
        <img src="${bank.img}" alt="${bank.name}" onerror="this.style.opacity=.3;this.style.filter='grayscale(1)';" />
        <div class="bank-name">${bank.name}</div>
      `;
      div.addEventListener('click', () => {
        // Save selected bank and go to bank details page
        localStorage.setItem('selectedBank', JSON.stringify(bank));
        window.location.href = 'bankdetails.html';
      });
      bankGrid.appendChild(div);
    });
  }

  renderBanks();
})();
