// SKIN QUIZ JS
let skinType = '';
let sensitive = '';
let goal = '';
let acne = '';
let skinFeel = '';
let makeup = '';
let sun = '';

let currentStep = 0;

function markActive(button) {
    const buttons = button.parentElement.querySelectorAll('button');
    buttons.forEach(btn => btn.classList.remove('active-option'));
    button.classList.add('active-option');
}

function selectOption(button, type) {
    skinType = type;
    markActive(button);
}

function setSensitive(value, button) {
    sensitive = value;
    markActive(button);
}

function setGoal(value, button) {
    goal = value;
    markActive(button);
}

function setAcne(value, button) {
    acne = value;
    markActive(button);
}

function setFeel(value, button) {
    skinFeel = value;
    markActive(button);
}

function setMakeup(value, button) {
    makeup = value;
    markActive(button);
}

function setSun(value, button) {
    sun = value;
    markActive(button);
}

function nextStep() {
    const steps = document.querySelectorAll('.quiz-step');
    if (currentStep < steps.length - 1) {
        steps[currentStep].classList.remove('active');
        currentStep++;
        steps[currentStep].classList.add('active');
        updateProgress();
    }
}

function prevStep() {
    const steps = document.querySelectorAll('.quiz-step');
    if (currentStep > 0) {
        steps[currentStep].classList.remove('active');
        currentStep--;
        steps[currentStep].classList.add('active');
        updateProgress();
    }
}

function updateProgress() {
    const progress = document.getElementById('progress');
    if (!progress) return;
    const percent = ((currentStep + 1) / document.querySelectorAll('.quiz-step').length) * 100;
    progress.style.width = percent + '%';
}

function showResult() {
    const result = document.getElementById('result');
    if (!skinType || !sensitive || !goal) {
        result.innerHTML = "Responda as perguntas principais antes de ver o resultado.";
        return;
    }

    let score = 80;
    if (skinType === "oleosa") score += 5;
    if (skinType === "seca") score += 5;
    if (sensitive === "sim") score -= 5;
    if (acne === "alta") score -= 10;
    if (skinFeel === "repuxando" && skinType === "seca") score += 10;
    if (sun === "alta") score += 3;

    let title = "";
    let description = "";
    let routine = [];

    if (goal === "hidratação" && skinType === "seca") {
        title = "Rotina Ultra Hidratação";
        description = "Recupera profundamente a barreira da pele.";
        routine = [
            "Gel de limpeza suave",
            "Sérum ácido hialurônico",
            "Creme reparador",
            "Protetor solar hidratante"
        ];
    } else if (goal === "glow") {
        title = "Rotina Glow Natural";
        description = "Realça luminosidade com leveza.";
        routine = [
            "Gel iluminador",
            "Sérum vitamina C",
            "Hidratante glow",
            "Protetor solar iluminador"
        ];
    } else {
        title = "Rotina Equilibrada";
        description = "Controle e equilíbrio para sua pele.";
        routine = [
            "Gel equilibrante",
            "Sérum multifuncional",
            "Hidratante leve",
            "Protetor solar diário"
        ];
    }

    let compatibility = Math.min(score, 99);

    result.innerHTML = `
        <div class="skin-result-card">
            <h2>${title}</h2>
            <p class="skin-desc">${description}</p>
            <div class="routine">
                ${routine.map((item, i) => `
                    <div class="step">${i+1}. ${item}</div>
                `).join('')}
            </div>
            <div class="compatibility-bar">
                <div style="width:${compatibility}%"></div>
            </div>
            <p>${compatibility}% de compatibilidade</p>
        </div>
    `;
}


// MENU HABURGUER MOBLIE
document.addEventListener('DOMContentLoaded', function() {
    const menuToggle = document.querySelector('.menu-toggle');
    const nav = document.querySelector('.navbar nav');

    if (menuToggle && nav) {
        menuToggle.addEventListener('click', function() {
            nav.classList.toggle('active');
        });
    }

    // Fechar menu ao clicar em um link
    const navLinks = document.querySelectorAll('.navbar nav a');
    navLinks.forEach(link => {
        link.addEventListener('click', function() {
            nav.classList.remove('active');
        });
    });


    //  DROPDOWN DO PERFIL
    
    const profileBtn = document.querySelector('.profile-btn');
    const dropdown = document.querySelector('.profile-dropdown');
    const profileMenu = document.querySelector('.profile-menu');

    if (profileBtn && dropdown && profileMenu) {
        profileBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            dropdown.classList.toggle('active');
        });

        document.addEventListener('click', function(e) {
            if (!profileMenu.contains(e.target)) {
                dropdown.classList.remove('active');
            }
        });
    }
});