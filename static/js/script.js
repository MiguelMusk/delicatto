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


// ADMIN - TABS, BUSCA E CONFIRMAÇÃO


document.addEventListener('DOMContentLoaded', function() {
    // Verifica se está na página admin
    const adminTabs = document.querySelector('.admin-tabs');
    if (!adminTabs) return;

    // ===== TABS =====
    const tabs = document.querySelectorAll('.admin-tab');
    const contents = document.querySelectorAll('.tab-content');

    tabs.forEach(tab => {
        tab.addEventListener('click', function() {
            tabs.forEach(t => t.classList.remove('active'));
            contents.forEach(c => c.classList.remove('active'));

            this.classList.add('active');
            const target = document.getElementById(this.dataset.tab);
            if (target) target.classList.add('active');
        });
    });

    // ===== BUSCA =====
    const searchInput = document.getElementById('searchProduto');
    const tableRows = document.querySelectorAll('#tableProdutos tr');

    if (searchInput) {
        searchInput.addEventListener('keyup', function() {
            const term = this.value.toLowerCase().trim();

            tableRows.forEach(row => {
                const nome = row.querySelector('td:nth-child(3)')?.textContent?.toLowerCase() || '';
                const id = row.querySelector('td:nth-child(1)')?.textContent?.toLowerCase() || '';

                if (nome.includes(term) || id.includes(term)) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        });
    }

    // ===== CONFIRMAÇÃO DE EXCLUSÃO =====
    const deleteBtns = document.querySelectorAll('.btn-delete');
    deleteBtns.forEach(btn => {
        btn.addEventListener('click', function(e) {
            const confirmar = confirm('Tem certeza que deseja excluir este produto?');
            if (!confirmar) {
                e.preventDefault();
            }
        });
    });
});
// ===== GRÁFICOS (Chart.js) =====

document.addEventListener('DOMContentLoaded', function() {
    // Verifica se está na página admin
    if (!document.querySelector('.admin-dashboard')) return;

    // ===== GRÁFICO 1 - Vendas =====
    const ctx1 = document.getElementById('chartVendas');
    if (ctx1) {
        new Chart(ctx1, {
            type: 'bar',
            data: {
                labels: ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom'],
                datasets: [{
                    label: 'Vendas (R$)',
                    data: [120, 250, 180, 320, 450, 280, 190],
                    backgroundColor: [
                        'rgba(143, 107, 207, 0.7)',
                        'rgba(143, 107, 207, 0.7)',
                        'rgba(143, 107, 207, 0.7)',
                        'rgba(143, 107, 207, 0.7)',
                        'rgba(143, 107, 207, 0.7)',
                        'rgba(143, 107, 207, 0.7)',
                        'rgba(143, 107, 207, 0.7)'
                    ],
                    borderColor: '#8F6BCF',
                    borderWidth: 2,
                    borderRadius: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(143, 107, 207, 0.05)'
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        }
                    }
                }
            }
        });
    }

    // ===== GRÁFICO 2 - Distribuição de Produtos =====
    const ctx2 = document.getElementById('chartProdutos');
    if (ctx2) {
        new Chart(ctx2, {
            type: 'doughnut',
            data: {
                labels: ['Séruns', 'Cremes', 'Protetores', 'Outros'],
                datasets: [{
                    data: [12, 8, 5, 3],
                    backgroundColor: [
                        '#8F6BCF',
                        '#B49CFF',
                        '#6d4eb0',
                        '#D4C4F0'
                    ],
                    borderWidth: 2,
                    borderColor: 'white'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 15,
                            usePointStyle: true,
                            pointStyle: 'circle',
                            font: {
                                size: 12
                            }
                        }
                    }
                },
                cutout: '60%'
            }
        });
    }
});

// ============================================
// ORDENAÇÃO DE TABELAS
// ============================================
function ordenarTabela(coluna, tabela) {
    const tbody = tabela === 'produtos' 
        ? document.getElementById('tableProdutos') 
        : document.getElementById('tableUsuarios');
    
    if (!tbody) return;

    const rows = Array.from(tbody.querySelectorAll('tr'));
    const header = tbody.closest('table').querySelectorAll('th')[coluna];
    const isAsc = header.classList.contains('asc');

    // Remove classes de todos os headers
    document.querySelectorAll('.sortable').forEach(th => {
        th.classList.remove('asc', 'desc');
    });

    // Ordena
    rows.sort((a, b) => {
        const valA = a.querySelectorAll('td')[coluna]?.textContent?.trim() || '';
        const valB = b.querySelectorAll('td')[coluna]?.textContent?.trim() || '';

        // Tenta converter para número
        const numA = parseFloat(valA.replace('R$', '').replace('#', '').trim());
        const numB = parseFloat(valB.replace('R$', '').replace('#', '').trim());

        if (!isNaN(numA) && !isNaN(numB)) {
            return isAsc ? numA - numB : numB - numA;
        }

        return isAsc ? valA.localeCompare(valB) : valB.localeCompare(valA);
    });

    // Adiciona classe de ordenação
    header.classList.add(isAsc ? 'desc' : 'asc');

    // Reinsere as linhas ordenadas
    rows.forEach(row => tbody.appendChild(row));
}

// ============================================
// NOTIFICAÇÕES
// ============================================
function fecharNotificacao(botao) {
    const alert = botao.closest('.alert');
    alert.style.animation = 'slideOutRight 0.4s ease';
    setTimeout(() => alert.remove(), 400);
}

// Fecha automaticamente após 5 segundos
document.addEventListener('DOMContentLoaded', function() {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            if (alert.parentNode) {
                alert.style.animation = 'slideOutRight 0.4s ease';
                setTimeout(() => alert.remove(), 400);
            }
        }, 5000);
    });
});

// CSS para animação de saída
const styleSheet = document.createElement('style');
styleSheet.textContent = `
    @keyframes slideOutRight {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
`;
document.head.appendChild(styleSheet);
// ============================================
// MOSTRAR/OCULTAR SENHA
// ============================================

function toggleSenha(inputId, button) {
    const input = document.getElementById(inputId);
    const icon = button.querySelector('i');

    if (input.type === 'password') {
        input.type = 'text';
        icon.classList.remove('fa-eye');
        icon.classList.add('fa-eye-slash');
    } else {
        input.type = 'password';
        icon.classList.remove('fa-eye-slash');
        icon.classList.add('fa-eye');
    }
}

// ============================================
// CARROSSEL DO MVV
// ============================================

document.addEventListener('DOMContentLoaded', function() {
    const track = document.getElementById('carouselTrack');
    const slides = document.querySelectorAll('.carousel-slide');
    const dotsContainer = document.getElementById('carouselDots');
    const prevBtn = document.getElementById('prevBtn');
    const nextBtn = document.getElementById('nextBtn');

    if (!track || slides.length === 0) return;

    let currentIndex = 0;
    const totalSlides = slides.length;

    // Criar dots
    slides.forEach((_, index) => {
        const dot = document.createElement('button');
        dot.classList.add('dot');
        if (index === 0) dot.classList.add('active');
        dot.addEventListener('click', () => goToSlide(index));
        dotsContainer.appendChild(dot);
    });

    const dots = document.querySelectorAll('.dot');

    function goToSlide(index) {
        if (index < 0) index = totalSlides - 1;
        if (index >= totalSlides) index = 0;
        currentIndex = index;
        track.style.transform = `translateX(-${currentIndex * 100}%)`;
        
        dots.forEach((dot, i) => {
            dot.classList.toggle('active', i === currentIndex);
        });
    }

    function nextSlide() {
        goToSlide(currentIndex + 1);
    }

    function prevSlide() {
        goToSlide(currentIndex - 1);
    }

    // Eventos dos botões
    if (nextBtn) nextBtn.addEventListener('click', nextSlide);
    if (prevBtn) prevBtn.addEventListener('click', prevSlide);

    // Teclado
    document.addEventListener('keydown', function(e) {
        if (e.key === 'ArrowRight') nextSlide();
        if (e.key === 'ArrowLeft') prevSlide();
    });

    // Swipe (touch)
    let touchStartX = 0;
    let touchEndX = 0;

    track.addEventListener('touchstart', function(e) {
        touchStartX = e.changedTouches[0].screenX;
    }, { passive: true });

    track.addEventListener('touchend', function(e) {
        touchEndX = e.changedTouches[0].screenX;
        const diff = touchStartX - touchEndX;
        if (Math.abs(diff) > 50) {
            if (diff > 0) nextSlide();
            else prevSlide();
        }
    }, { passive: true });
});
// ============================================
// CARRINHO FLUTUANTE COM POPUP
// ============================================

document.addEventListener('DOMContentLoaded', function() {
    const cartBtn = document.getElementById('floatingCartBtn');
    const popup = document.getElementById('floatingCartPopup');
    const closeBtn = document.getElementById('closePopup');

    if (!cartBtn || !popup) return;

    // Abrir ao clicar no botão
    cartBtn.addEventListener('click', function(e) {
        e.preventDefault();
        popup.classList.toggle('active');
    });

    // Fechar ao clicar no X
    if (closeBtn) {
        closeBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            popup.classList.remove('active');
        });
    }

    // Fechar ao clicar fora
    document.addEventListener('click', function(e) {
        if (!popup.contains(e.target) && !cartBtn.contains(e.target)) {
            popup.classList.remove('active');
        }
    });

    // Fechar ao pressionar ESC
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            popup.classList.remove('active');
        }
    });
});

// ============================================
// SCROLL REVEAL - ANIMAÇÃO AO ROLAR A PÁGINA
// ============================================

document.addEventListener('DOMContentLoaded', function() {
    const reveals = document.querySelectorAll('.reveal');

    function checkReveal() {
        const windowHeight = window.innerHeight;
        const revealPoint = 150;

        reveals.forEach(element => {
            const revealTop = element.getBoundingClientRect().top;

            if (revealTop < windowHeight - revealPoint) {
                element.classList.add('active');
            }
        });
    }

    // Verifica ao carregar
    checkReveal();

    // Verifica ao rolar
    window.addEventListener('scroll', checkReveal);
});