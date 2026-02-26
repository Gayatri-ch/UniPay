const consentCheckbox = document.getElementById('consentCheckbox');
const nextBtn = document.getElementById('nextBtn');

nextBtn.addEventListener('click', () => {
    if (!consentCheckbox.checked) {
        alert("Please agree to share bank details first.");
        return;
    }
    localStorage.setItem('bankConsent', 'true');
    window.location.href = 'selectbank.html';
});
