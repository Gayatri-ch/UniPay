const selectedBank = JSON.parse(localStorage.getItem('selectedBank'));
if (!selectedBank) {
    alert("Please select a bank first.");
    window.location.href = 'selectbank.html';
}

const bankNameEl = document.getElementById('bankName');
const accNumberEl = document.getElementById('accNumber');
const ifscPrefixEl = document.getElementById('ifscPrefix');
const ifscSuffixEl = document.getElementById('ifscSuffix');
const ifscFullEl = document.getElementById('ifscFull');
const branchNameEl = document.getElementById('branchName');
const confirmShareEl = document.getElementById('confirmShare');
const bankForm = document.getElementById('bankForm');

bankNameEl.textContent = selectedBank.name;
ifscPrefixEl.value = selectedBank.prefix.toUpperCase();

// Update IFSC & branch automatically
ifscSuffixEl.addEventListener('input', () => {
    const cleaned = ifscSuffixEl.value.replace(/[^A-Z0-9]/gi,'').slice(0,7).toUpperCase();
    ifscSuffixEl.value = cleaned;
    ifscFullEl.textContent = cleaned ? `${selectedBank.prefix}${cleaned}` : '—';
    if (cleaned.length >= 3) {
        let seed = 0;
        for (let i = 0; i < cleaned.length; i++) seed += cleaned.charCodeAt(i);
        const idx = seed % selectedBank.branches.length;
        branchNameEl.value = selectedBank.branches[idx];
    } else {
        branchNameEl.value = '';
    }
});

// Form submit
bankForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const acc = accNumberEl.value.trim();
    const ifsc = (ifscPrefixEl.value + ifscSuffixEl.value.trim()).toUpperCase();
    if (!/^\d{6,20}$/.test(acc)) { alert("Enter valid account number."); return; }
    if (!/^[A-Z0-9]{7}$/.test(ifscSuffixEl.value)) { alert("Enter valid IFSC suffix."); return; }
    if (!confirmShareEl.checked) { alert("Please confirm details."); return; }

    const payload = {
        bankCode: selectedBank.code,
        bankName: selectedBank.name,
        account: acc,
        ifsc,
        branch: branchNameEl.value,
        linkedOn: new Date().toISOString()
    };

    const list = JSON.parse(localStorage.getItem('linkedBanks') || '[]');
    list.push(payload);
    localStorage.setItem('linkedBanks', JSON.stringify(list));

    alert(`Bank ${selectedBank.name} linked successfully!`);
    window.location.href = 'selectbank.html';
});

// Add this to make the back button work
function goBack() {
    window.location.href = 'selectbank.html';
}
