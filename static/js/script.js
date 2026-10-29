// SKIN QUIZ JS
let skinType = '';
let sensitive = '';
let goal = '';
let acne = '';
let skinFeel = '';
let makeup = '';
let sun = '';

let currentStep = 0;

// ===== NOVO: mapa de respostas por pergunta =====
// Chave = índice do passo (0 a 6), valor = true quando respondido
let respostas = {
    0: false,  // Tipo de pele
    1: false,  // Sensibilidade
    2: false,  // Objetivo
    3: false,  // Acne
    4: false,  // Sensação após lavar
    5: false,  // Maquiagem
    6: false   // Sol
};


function markActive(button) {
    const buttons = button.parentElement.querySelectorAll('button');
    buttons.forEach(btn => btn.classList.remove('active-option'));
    button.classList.add('active-option');
}


// ===== NOVO: habilita o botão "Próxima" do passo atual =====
function habilitarProxima() {
    const stepAtual = document.querySelectorAll('.quiz-step')[currentStep];
    if (!stepAtual) return;

    // Marca a resposta como preenchida
    respostas[currentStep] = true;

    // Habilita todos os botões de avanço dentro do passo (next-btn e result-btn)
    stepAtual.querySelectorAll('.next-btn, .result-btn').forEach(btn => {
        btn.disabled = false;
        btn.classList.remove('disabled');
    });
}


// ===== NOVO: verifica se o passo atual foi respondido =====
function passoRespondido(index) {
    return respostas[index] === true;
}


function selectOption(button, type) {
    skinType = type;
    markActive(button);
    habilitarProxima();
}

function setSensitive(value, button) {
    sensitive = value;
    markActive(button);
    habilitarProxima();
}

function setGoal(value, button) {
    goal = value;
    markActive(button);
    habilitarProxima();
}

function setAcne(value, button) {
    acne = value;
    markActive(button);
    habilitarProxima();
}

function setFeel(value, button) {
    skinFeel = value;
    markActive(button);
    habilitarProxima();
}

function setMakeup(value, button) {
    makeup = value;
    markActive(button);
    habilitarProxima();
}

function setSun(value, button) {
    sun = value;
    markActive(button);
    habilitarProxima();
}


// ===== ATUALIZADO: bloqueia avanço sem resposta =====
function nextStep() {
    // Verifica se o passo atual foi respondido
    if (!passoRespondido(currentStep)) {
        mostrarAvisoPasso(currentStep);
        return;
    }

    const steps = document.querySelectorAll('.quiz-step');
    if (currentStep < steps.length - 1) {
        steps[currentStep].classList.remove('active');
        currentStep++;
        steps[currentStep].classList.add('active');

        // Desabilita o botão do novo passo até que ele seja respondido
        bloquearBotoesPasso(currentStep);

        updateProgress();
        scrollParaQuiz();
    }
}

function prevStep() {
    const steps = document.querySelectorAll('.quiz-step');
    if (currentStep > 0) {
        steps[currentStep].classList.remove('active');
        currentStep--;
        steps[currentStep].classList.add('active');
        updateProgress();
        scrollParaQuiz();
    }
}


// ===== NOVO: bloqueia os botões de avanço de um passo =====
function bloquearBotoesPasso(index) {
    const step = document.querySelectorAll('.quiz-step')[index];
    if (!step) return;

    step.querySelectorAll('.next-btn, .result-btn').forEach(btn => {
        // Se já foi respondido, mantém habilitado
        if (!passoRespondido(index)) {
            btn.disabled = true;
            btn.classList.add('disabled');
        } else {
            btn.disabled = false;
            btn.classList.remove('disabled');
        }
    });
}


// ===== NOVO: mostra aviso visual quando tenta avançar sem responder =====
function mostrarAvisoPasso(index) {
    const step = document.querySelectorAll('.quiz-step')[index];
    if (!step) return;

    // Remove aviso anterior (se existir)
    const avisoAntigo = step.querySelector('.quiz-warning');
    if (avisoAntigo) avisoAntigo.remove();

    // Cria aviso
    const aviso = document.createElement('div');
    aviso.className = 'quiz-warning';
    aviso.innerHTML = '⚠️ Escolha uma opção para continuar';
    step.querySelector('.quiz-step-header').appendChild(aviso);

    // Anima e remove
    setTimeout(() => aviso.classList.add('show'), 10);
    setTimeout(() => {
        aviso.classList.remove('show');
        setTimeout(() => aviso.remove(), 300);
    }, 2500);
}


// ===== NOVO: scroll suave para o topo do quiz ao trocar de passo =====
function scrollParaQuiz() {
    const quizBox = document.querySelector('.quiz-box');
    if (quizBox) {
        const offset = 120;
        const top = quizBox.getBoundingClientRect().top + window.pageYOffset - offset;
        window.scrollTo({ top, behavior: 'smooth' });
    }
}


// ===== ATUALIZADO: contador e percentual =====
function updateProgress() {
    const progress = document.getElementById('progress');
    if (!progress) return;

    const total = document.querySelectorAll('.quiz-step').length;
    const percent = ((currentStep + 1) / total) * 100;

    progress.style.width = percent + '%';

    const currentStepEl = document.getElementById('currentStep');
    const totalStepsEl = document.getElementById('totalSteps');
    const progressPercentEl = document.getElementById('progressPercent');

    if (currentStepEl) currentStepEl.textContent = currentStep + 1;
    if (totalStepsEl) totalStepsEl.textContent = total;
    if (progressPercentEl) progressPercentEl.textContent = Math.round(percent) + '%';
}


// ============================================
// SHOW RESULT - VERSÃO HÍBRIDA (IA + ESTÁTICO)
// ============================================
async function showResult() {
    const result = document.getElementById('result');
    if (!result) return;

    // ===== VALIDAÇÃO: último passo respondido? =====
    if (!passoRespondido(currentStep)) {
        mostrarAvisoPasso(currentStep);
        return;
    }

    // Validação mínima de segurança (garante que nada ficou para trás)
    if (!skinType || !sensitive || !goal) {
        result.innerHTML = `
            <div class="skin-result-card">
                <p style="color:#dc3545;text-align:center;">⚠️ Responda as perguntas principais antes de ver o resultado.</p>
            </div>
        `;
        return;
    }

    // ===== 1. DEFINE TÍTULO, PRODUTOS E ROTINA (LÓGICA ESTÁTICA) =====
    let title = "";
    let description = "";
    let routine = [];
    let produtos = [];

    if (goal === "hidratacao" && skinType === "seca") {
        title = "Rotina Ultra Hidratação";
        description = "Recupera profundamente a barreira da pele, devolvendo maciez e viço.";
        routine = ["Gel de limpeza suave", "Sérum ácido hialurônico", "Creme reparador", "Protetor solar hidratante"];
        produtos = [
            { nome: "Hidratante Corporal", preco: "R$ 89,90", link: "/produto/1" },
            { nome: "Sérum Facial", preco: "R$ 129,90", link: "/produto/2" },
            { nome: "Creme Revitalizante", preco: "R$ 99,90", link: "/produto/3" }
        ];
    }
    else if (goal === "glow") {
        title = "Rotina Glow Natural";
        description = "Realça luminosidade com leveza, deixando sua pele radiante e uniforme.";
        routine = ["Gel iluminador", "Sérum vitamina C", "Hidratante glow", "Protetor solar iluminador"];
        produtos = [
            { nome: "Glow Skin Essence", preco: "R$ 94,90", link: "/produto/4" },
            { nome: "Sérum Facial", preco: "R$ 129,90", link: "/produto/2" }
        ];
    }
    else if (goal === "oleosidade" && skinType === "oleosa") {
        title = "Rotina Equilíbrio e Controle";
        description = "Controla a oleosidade sem agredir a pele, mantendo o equilíbrio natural.";
        routine = ["Gel de limpeza profunda", "Tônico adstringente", "Sérum matificante", "Protetor solar oil-free"];
        produtos = [
            { nome: "Sérum Facial", preco: "R$ 129,90", link: "/produto/2" },
            { nome: "Body Splash", preco: "R$ 79,90", link: "/produto/5" }
        ];
    }
    else if (goal === "antiidade") {
        title = "Rotina Anti-idade";
        description = "Combate os sinais do envelhecimento com ativos poderosos e nutrição profunda.";
        routine = ["Gel de limpeza suave", "Sérum retinol", "Creme rejuvenescedor", "Protetor solar com FPS 50"];
        produtos = [
            { nome: "Creme Revitalizante", preco: "R$ 99,90", link: "/produto/3" },
            { nome: "Sérum Facial", preco: "R$ 129,90", link: "/produto/2" }
        ];
    }
    else if (skinType === "mista") {
        title = "Rotina Equilibrada";
        description = "Combina hidratação e controle para peles mistas, tratando cada área de forma específica.";
        routine = ["Gel de limpeza equilibrador", "Sérum multifuncional", "Hidratante leve", "Protetor solar diário"];
        produtos = [
            { nome: "Hidratante Corporal", preco: "R$ 89,90", link: "/produto/1" },
            { nome: "Body Splash", preco: "R$ 79,90", link: "/produto/5" }
        ];
    }
    else {
        title = "Rotina Essencial";
        description = "Cuidados básicos para manter sua pele saudável e protegida.";
        routine = ["Gel de limpeza suave", "Sérum multifuncional", "Hidratante leve", "Protetor solar diário"];
        produtos = [
            { nome: "Hidratante Corporal", preco: "R$ 89,90", link: "/produto/1" }
        ];
    }

    // ===== 2. CALCULA COMPATIBILIDADE =====
    let score = 80;
    if (skinType === "oleosa") score += 5;
    if (skinType === "seca") score += 5;
    if (sensitive === "sim") score -= 5;
    if (acne === "alta") score -= 10;
    if (skinFeel === "repuxando" && skinType === "seca") score += 10;
    if (sun === "alta") score += 3;
    const compatibility = Math.min(score, 99);

    // ===== 3. MOSTRA LOADING =====
    result.innerHTML = `
        <div class="skin-result-card">
            <div class="result-header">
                <span class="result-badge">
                    <i class="fa-solid fa-wand-magic-sparkles"></i>
                    Analisando seu perfil...
                </span>
                <h2>${title}</h2>
                <p class="skin-desc">${description}</p>
            </div>
            <div style="text-align:center;padding:50px 20px;">
                <div class="loader-spinner" style="margin:0 auto 20px;"></div>
                <p style="color:#8a7a9e;font-size:14px;"> Gerando diagnóstico personalizado com IA...</p>
            </div>
        </div>
    `;
    result.scrollIntoView({ behavior: 'smooth', block: 'start' });

    // ===== 4. CHAMA A IA =====
    let diagnosticoIA = null;
    try {
        const perfil = {
            tipo_pele: skinType,
            sensivel: sensitive,
            objetivo: goal,
            acne: acne || 'baixa',
            sente_apos_lavar: skinFeel || 'normal',
            maquiagem: makeup || 'baixo',
            exposicao_sol: sun || 'media'
        };

        const response = await fetch('/api/skinmatch/diagnostico', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(perfil)
        });

        const data = await response.json();
        if (!data.erro && data.diagnostico) {
            diagnosticoIA = data.diagnostico;
        }
    } catch (e) {
        console.warn('IA indisponível, usando apenas lógica estática:', e);
    }

    // ===== 5. FORMATA O DIAGNÓSTICO =====
    let blocoIA = '';

    if (diagnosticoIA) {
        const textoFormatado = diagnosticoIA
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\n\n/g, '</p><p>')
            .replace(/\n/g, '<br>');

        blocoIA = `
            <div class="result-explicacao">
                <h4><i class="fa-solid fa-stethoscope"></i> Análise da IA Dermatológica</h4>
                <div style="line-height:1.85;color:#4a3a5a;font-size:15px;">
                    <p>${textoFormatado}</p>
                </div>
            </div>
        `;
    } else {
        blocoIA = `
            <div class="result-explicacao">
                <h4><i class="fa-solid fa-circle-info"></i> Análise da IA Dermatológica</h4>
                <p style="color:#6f6878;font-size:14px;margin:0;line-height:1.6;">
                    Não foi possível gerar a análise textual agora. Mas sua rotina personalizada está logo abaixo! 💜
                </p>
            </div>
        `;
    }

    // ===== 6. MONTA O CARD FINAL =====
    result.innerHTML = `
        <div class="skin-result-card">
            <div class="result-header">
                <span class="result-badge">
                    <i class="fa-solid fa-sparkles"></i>
                    Sua rotina personalizada
                </span>
                <h2>${title}</h2>
                <p class="skin-desc">${description}</p>
            </div>

            ${blocoIA}

            <div class="routine">
                <h4><i class="fa-solid fa-list-check"></i> Passos da sua rotina</h4>
                ${routine.map((item, i) => `
                    <div class="step">
                        <span class="step-number">${i + 1}</span>
                        <span class="step-text">${item}</span>
                    </div>
                `).join('')}
            </div>

            <div class="produtos-recomendados">
                <h4><i class="fa-solid fa-gem"></i> Produtos recomendados para você</h4>
                <div class="produtos-grid">
                    ${produtos.map(produto => `
                        <div class="produto-item">
                            <span class="produto-nome">${produto.nome}</span>
                            <span class="produto-preco">${produto.preco}</span>
                            <a href="${produto.link}" class="produto-btn">
                                <i class="fa-solid fa-eye"></i> Ver Produto
                            </a>
                        </div>
                    `).join('')}
                </div>
            </div>

            <div class="compatibility-section">
                <div class="compatibility-label">
                    <span>Compatibilidade com seu perfil</span>
                    <span>${compatibility}%</span>
                </div>
                <div class="compatibility-bar">
                    <div style="width:${compatibility}%"></div>
                </div>
                <p class="compatibility-text">Essa rotina é altamente compatível com o perfil da sua pele.</p>
            </div>

            <div class="result-actions">
                <a href="/produtos" class="btn-primary">
                    <i class="fa-solid fa-bag-shopping"></i> Ver todos os produtos
                </a>
                <button class="btn-secondary" onclick="reiniciarSkinmatch()">
                    <i class="fa-solid fa-rotate"></i> Refazer o teste
                </button>
            </div>

            <p style="font-size:11px;color:#8a7a9e;margin-top:20px;text-align:center;line-height:1.6;">
                ⚠️ Esta é uma análise fictícia gerada por IA para fins de demonstração.
                Não substitui a consulta com um dermatologista profissional.
            </p>
        </div>
    `;

    result.scrollIntoView({ behavior: 'smooth', block: 'start' });
}


// ===== FUNÇÃO PARA REINICIAR =====
function reiniciarSkinmatch() {
    // Limpa as variáveis
    skinType = '';
    sensitive = '';
    goal = '';
    acne = '';
    skinFeel = '';
    makeup = '';
    sun = '';
    currentStep = 0;

    // ===== NOVO: reseta as respostas =====
    respostas = {
        0: false,
        1: false,
        2: false,
        3: false,
        4: false,
        5: false,
        6: false
    };

    // Reseta o progresso
    const progress = document.getElementById('progress');
    if (progress) progress.style.width = '14%';

    // Mostra o primeiro passo
    const steps = document.querySelectorAll('.quiz-step');
    steps.forEach((step, index) => {
        step.classList.toggle('active', index === 0);

        // Remove avisos antigos
        const aviso = step.querySelector('.quiz-warning');
        if (aviso) aviso.remove();
    });

    // Limpa o resultado
    const result = document.getElementById('result');
    if (result) result.innerHTML = '';

    // Remove a classe active-option de todos os botões
    document.querySelectorAll('.options button').forEach(btn => {
        btn.classList.remove('active-option');
    });

    // ===== NOVO: bloqueia todos os botões de avanço =====
    for (let i = 0; i < steps.length; i++) {
        bloquearBotoesPasso(i);
    }

    // Atualiza o contador
    updateProgress();

    // Rola para o topo do quiz
    const quizBox = document.querySelector('.quiz-box');
    if (quizBox) quizBox.scrollIntoView({ behavior: 'smooth', block: 'start' });
}


// ============================================
// INICIALIZAÇÃO
// ============================================
document.addEventListener('DOMContentLoaded', function() {
    // Só executa se estiver na página de skinmatch
    if (!document.querySelector('.quiz-box')) return;

    // Define o total de passos
    const totalSteps = document.querySelectorAll('.quiz-step').length;
    const totalStepsEl = document.getElementById('totalSteps');
    if (totalStepsEl) totalStepsEl.textContent = totalSteps;

    // Inicializa contador
    const currentStepEl = document.getElementById('currentStep');
    const progressPercentEl = document.getElementById('progressPercent');
    if (currentStepEl) currentStepEl.textContent = '1';
    if (progressPercentEl) progressPercentEl.textContent = Math.round(100 / totalSteps) + '%';

    // ===== NOVO: bloqueia todos os botões de avanço inicialmente =====
    for (let i = 0; i < totalSteps; i++) {
        bloquearBotoesPasso(i);
    }
});


// ============================================
// SUSTENTABILIDADE - ANIMAÇÃO DOS NÚMEROS
// ============================================

document.addEventListener('DOMContentLoaded', function() {
    const stats = document.querySelectorAll('.sust-stat-number');
    if (stats.length === 0) return;

    const animateNumber = (element) => {
        const target = parseInt(element.getAttribute('data-target'));
        const duration = 2000;
        const step = target / (duration / 16);
        let current = 0;

        const timer = setInterval(() => {
            current += step;
            if (current >= target) {
                current = target;
                clearInterval(timer);
            }
            element.textContent = Math.floor(current);
        }, 16);
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                animateNumber(entry.target);
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.5 });

    stats.forEach(stat => observer.observe(stat));
});


// ============================================
// VALIDAÇÃO DO CADASTRO - TERMOS DE USO
// ============================================

document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('cadastroForm');
    const checkbox = document.getElementById('aceitoTermos');
    const termsError = document.getElementById('termsError');

    if (termsError) termsError.style.display = 'none';

    if (checkbox) {
        checkbox.addEventListener('change', function() {
            if (this.checked) {
                termsError.style.display = 'none';
                this.closest('.terms-group').classList.remove('error');
            }
        });
    }

    if (form) {
        form.addEventListener('submit', function(e) {
            if (!checkbox.checked) {
                e.preventDefault();
                termsError.style.display = 'block';
                checkbox.closest('.terms-group').classList.add('error');
                checkbox.focus();
                termsError.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        });
    }
});


// ============================================
// TELA DE CARREGAMENTO
// ============================================

document.addEventListener('DOMContentLoaded', function() {
    const loadingScreen = document.getElementById('loading-screen');
    if (loadingScreen) {
        setTimeout(function() {
            loadingScreen.classList.add('hidden');
        }, 500);
    }

    const links = document.querySelectorAll('a:not([target="_blank"]):not([href^="#"]):not([href^="http"])');
    links.forEach(function(link) {
        link.addEventListener('click', function(e) {
            const href = this.getAttribute('href');

            if (href && href.includes('/adicionar_carrinho/')) return;
            if (href && href.includes('/api/')) return;
            if (this.id === 'floatingCartBtn') return;

            if (this.classList.contains('popup-checkout') ||
                this.classList.contains('popup-checkout-finalizar') ||
                this.classList.contains('popup-empty-btn')) {
                return;
            }

            if (this.classList.contains('btn-cart')) return;

            if (href && href !== '' && href !== '#' && !href.startsWith('http') && loadingScreen) {
                loadingScreen.classList.remove('hidden');
            }
        });
    });
});


// ============================================
// MENU HAMBURGUER + DROPDOWN PERFIL
// ============================================

document.addEventListener('DOMContentLoaded', function() {
    const menuToggle = document.querySelector('.menu-toggle');
    const nav = document.querySelector('.navbar nav');

    if (menuToggle && nav) {
        menuToggle.addEventListener('click', function() {
            nav.classList.toggle('active');
        });
    }

    const navLinks = document.querySelectorAll('.navbar nav a');
    navLinks.forEach(link => {
        link.addEventListener('click', function() {
            nav.classList.remove('active');
        });
    });

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


// ============================================
// ADMIN - TABS, BUSCA E GRÁFICOS
// ============================================

document.addEventListener('DOMContentLoaded', function() {
    if (!document.querySelector('.admin-dashboard')) return;

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

    // ===== BUSCA DE PRODUTOS =====
    const searchInput = document.getElementById('searchProduto');
    const tableRows = document.querySelectorAll('#tableProdutos tr');

    if (searchInput) {
        searchInput.addEventListener('keyup', function() {
            const term = this.value.toLowerCase().trim();
            tableRows.forEach(row => {
                const nome = row.querySelector('td:nth-child(3)')?.textContent?.toLowerCase() || '';
                const id = row.querySelector('td:nth-child(1)')?.textContent?.toLowerCase() || '';
                row.style.display = (nome.includes(term) || id.includes(term)) ? '' : 'none';
            });
        });
    }

    // ===== BUSCA DE USUÁRIOS =====
    const searchUsuario = document.getElementById('searchUsuario');
    const userRows = document.querySelectorAll('#tableUsuarios tr');

    if (searchUsuario) {
        searchUsuario.addEventListener('keyup', function() {
            const term = this.value.toLowerCase().trim();
            userRows.forEach(row => {
                const nome = row.querySelector('td:nth-child(2)')?.textContent?.toLowerCase() || '';
                const email = row.querySelector('td:nth-child(3)')?.textContent?.toLowerCase() || '';
                row.style.display = (nome.includes(term) || email.includes(term)) ? '' : 'none';
            });
        });
    }

    // ===== CONFIRMAÇÃO DE EXCLUSÃO =====
    document.querySelectorAll('.btn-delete').forEach(btn => {
        btn.addEventListener('click', function(e) {
            if (!confirm('Tem certeza que deseja excluir este produto?')) {
                e.preventDefault();
            }
        });
    });

    // ============================================
    // GRÁFICOS
    // ============================================
    if (window.dadosAdmin) {
        criarGraficos(window.dadosAdmin.vendas, window.dadosAdmin.distribuicao);
    }
});

function criarGraficos(vendasSemana, distribuicao) {
    // ===== GRÁFICO 1: VENDAS =====
    const canvasVendas = document.getElementById('chartVendas');
    if (canvasVendas) {
        let labels = ['Sem dados'];
        let valores = [0];

        if (vendasSemana && vendasSemana.length > 0) {
            labels = [];
            valores = [];
            vendasSemana.forEach(item => {
                // item[0] = data, item[1] = total_pedidos, item[2] = valor_total
                const data = new Date(item[0] + 'T00:00:00');
                const diaMes = data.getDate().toString().padStart(2, '0') + '/' + (data.getMonth() + 1).toString().padStart(2, '0');
                labels.push(diaMes);
                valores.push(parseFloat(item[2]) || 0);
            });
        }

        new Chart(canvasVendas, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Vendas (R$)',
                    data: valores,
                    backgroundColor: 'rgba(143, 107, 207, 0.7)',
                    borderColor: '#8F6BCF',
                    borderWidth: 2,
                    borderRadius: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    y: { 
                        beginAtZero: true,
                        ticks: { callback: v => 'R$ ' + v }
                    }
                }
            }
        });
    }

    // ===== GRÁFICO 2: DISTRIBUIÇÃO =====
    const canvasDistrib = document.getElementById('chartProdutos');
    if (canvasDistrib) {
        let labels = ['Nenhum produto'];
        let dados = [1];
        let cores = ['#e0d4f0'];
        const coresPaleta = ['#8F6BCF', '#B49CFF', '#6d4eb0', '#D4C4F0', '#E8D5FF'];

        if (distribuicao && distribuicao.length > 0) {
            labels = [];
            dados = [];
            cores = [];
            distribuicao.forEach((item, index) => {
                // item[0] = categoria, item[1] = total
                labels.push(item[0] || 'Outros');
                dados.push(parseInt(item[1]) || 0);
                cores.push(coresPaleta[index % coresPaleta.length]);
            });
        }

        new Chart(canvasDistrib, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: dados,
                    backgroundColor: cores,
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
                            font: { size: 12 }
                        }
                    }
                },
                cutout: '60%'
            }
        });
    }
}

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

    document.querySelectorAll('.sortable').forEach(th => {
        th.classList.remove('asc', 'desc');
    });

    rows.sort((a, b) => {
        const valA = a.querySelectorAll('td')[coluna]?.textContent?.trim() || '';
        const valB = b.querySelectorAll('td')[coluna]?.textContent?.trim() || '';

        const numA = parseFloat(valA.replace('R$', '').replace('#', '').trim());
        const numB = parseFloat(valB.replace('R$', '').replace('#', '').trim());

        if (!isNaN(numA) && !isNaN(numB)) {
            return isAsc ? numA - numB : numB - numA;
        }
        return isAsc ? valA.localeCompare(valB) : valB.localeCompare(valA);
    });

    header.classList.add(isAsc ? 'desc' : 'asc');
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

    function nextSlide() { goToSlide(currentIndex + 1); }
    function prevSlide() { goToSlide(currentIndex - 1); }

    if (nextBtn) nextBtn.addEventListener('click', nextSlide);
    if (prevBtn) prevBtn.addEventListener('click', prevSlide);

    document.addEventListener('keydown', function(e) {
        if (e.key === 'ArrowRight') nextSlide();
        if (e.key === 'ArrowLeft') prevSlide();
    });

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

    cartBtn.addEventListener('click', function(e) {
        e.preventDefault();
        popup.classList.toggle('active');
    });

    if (closeBtn) {
        closeBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            popup.classList.remove('active');
        });
    }

    document.addEventListener('click', function(e) {
        if (!popup.contains(e.target) && !cartBtn.contains(e.target)) {
            popup.classList.remove('active');
        }
    });

    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            popup.classList.remove('active');
        }
    });
});


// ============================================
// PERSONALIZAÇÃO - PREVIEW AO VIVO
// ============================================

document.addEventListener('DOMContentLoaded', function() {
    const nomeInput = document.getElementById('nomeRotulo');
    const mensagemInput = document.getElementById('mensagemRotulo');
    const previewNome = document.getElementById('previewNome');
    const previewProduto = document.getElementById('previewProduto');
    const previewPele = document.getElementById('previewPele');
    const previewFragrancia = document.getElementById('previewFragrancia');
    const previewObjetivo = document.getElementById('previewObjetivo');
    const previewMensagem = document.getElementById('previewMensagem');
    const previewPreco = document.getElementById('previewPreco');
    const previewProdutoContainer = document.getElementById('produtoPreview');
    const previewRotulo = document.getElementById('previewRotulo');
    const charCounter = document.getElementById('charCounter');
    const msgCounter = document.getElementById('msgCounter');

    if (nomeInput && charCounter) {
        nomeInput.addEventListener('input', function() {
            const length = this.value.length;
            charCounter.textContent = length + '/20';
            charCounter.style.color = length > 18 ? '#dc3545' : '#8a7a9e';
        });
    }

    if (mensagemInput && msgCounter) {
        mensagemInput.addEventListener('input', function() {
            const length = this.value.length;
            msgCounter.textContent = length + '/100';
            msgCounter.style.color = length > 90 ? '#dc3545' : '#8a7a9e';
        });
    }

    if (nomeInput && previewNome) {
        nomeInput.addEventListener('input', function() {
            previewNome.textContent = this.value.trim() || 'Seu Nome';
        });
    }

    if (mensagemInput && previewMensagem) {
        mensagemInput.addEventListener('input', function() {
            previewMensagem.textContent = this.value.trim() || '';
        });
    }

    document.querySelectorAll('input[name="produto_base"]').forEach(function(radio) {
        radio.addEventListener('change', function() {
            if (this.checked) {
                const nome = this.getAttribute('data-nome') || 'Produto';
                const preco = this.getAttribute('data-preco') || '0.00';
                previewProduto.textContent = nome.toUpperCase();
                previewPreco.textContent = 'R$ ' + parseFloat(preco).toFixed(2).replace('.', ',');
            }
        });
    });

    const peleSelect = document.getElementById('selectPele');
    if (peleSelect && previewPele) {
        peleSelect.addEventListener('change', function() {
            previewPele.textContent = this.options[this.selectedIndex].text;
        });
    }

    const fragranciaSelect = document.getElementById('selectFragrancia');
    if (fragranciaSelect && previewFragrancia) {
        fragranciaSelect.addEventListener('change', function() {
            previewFragrancia.textContent = this.options[this.selectedIndex].text;
        });
    }

    const objetivoSelect = document.getElementById('selectObjetivo');
    if (objetivoSelect && previewObjetivo) {
        objetivoSelect.addEventListener('change', function() {
            previewObjetivo.textContent = this.options[this.selectedIndex].text;
        });
    }

    document.querySelectorAll('input[name="cor_embalagem"]').forEach(function(radio) {
        radio.addEventListener('change', function() {
            if (this.checked) {
                const cor = this.getAttribute('data-cor') || '#6d4eb0';
                previewProdutoContainer.style.background = cor;
            }
        });
    });

    document.querySelectorAll('input[name="cor_fonte"]').forEach(function(radio) {
        radio.addEventListener('change', function() {
            if (this.checked) {
                const corTexto = this.getAttribute('data-texto') || '#ffffff';

                previewRotulo.style.color = corTexto;
                previewNome.style.color = corTexto;
                previewProduto.style.color = corTexto;
                previewPele.style.color = corTexto;
                previewFragrancia.style.color = corTexto;
                previewObjetivo.style.color = corTexto;
                previewMensagem.style.color = corTexto;

                document.querySelectorAll('.preview-divider').forEach(function(el) {
                    el.style.color = corTexto;
                    el.style.opacity = '0.3';
                });
            }
        });
    });

    setTimeout(function() {
        const checkedProduto = document.querySelector('input[name="produto_base"]:checked');
        if (checkedProduto) {
            const nome = checkedProduto.getAttribute('data-nome') || 'Produto';
            const preco = checkedProduto.getAttribute('data-preco') || '0.00';
            previewProduto.textContent = nome.toUpperCase();
            previewPreco.textContent = 'R$ ' + parseFloat(preco).toFixed(2).replace('.', ',');
        }

        const corInicial = document.querySelector('input[name="cor_embalagem"]:checked');
        if (corInicial) {
            const cor = corInicial.getAttribute('data-cor') || '#6d4eb0';
            previewProdutoContainer.style.background = cor;
        }

        const fonteInicial = document.querySelector('input[name="cor_fonte"]:checked');
        if (fonteInicial) {
            const corTexto = fonteInicial.getAttribute('data-texto') || '#ffffff';
            previewRotulo.style.color = corTexto;
            previewNome.style.color = corTexto;
            previewProduto.style.color = corTexto;
            previewPele.style.color = corTexto;
            previewFragrancia.style.color = corTexto;
            previewObjetivo.style.color = corTexto;
            previewMensagem.style.color = corTexto;
        }
    }, 100);
});

// ============================================
// PERFIL - AVATAR E CONFIGURAÇÕES
// ============================================

document.addEventListener('DOMContentLoaded', function() {
    // ===== Avatar com iniciais =====
    const avatar = document.getElementById('perfilAvatar');
    if (avatar) {
        const nome = avatar.dataset.nome || '';
        const partes = nome.trim().split(' ').filter(p => p.length > 0);
        let iniciais = '';

        if (partes.length === 1) {
            iniciais = partes[0][0].toUpperCase();
        } else if (partes.length > 1) {
            iniciais = (partes[0][0] + partes[partes.length - 1][0]).toUpperCase();
        }

        avatar.textContent = iniciais;
    }
});


// Toggle das abas de configuração
function toggleConfig(id) {
    const form = document.getElementById(id);
    if (!form) return;

    form.classList.toggle('active');

    const card = form.closest('.perfil-config-card');
    const chevron = card.querySelector('.perfil-chevron');
    if (chevron) {
        chevron.style.transform = form.classList.contains('active')
            ? 'rotate(180deg)'
            : 'rotate(0deg)';
    }
}
// ============================================
// SCROLL REVEAL
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

    checkReveal();
    window.addEventListener('scroll', checkReveal);
});