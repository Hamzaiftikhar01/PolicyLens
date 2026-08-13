// POLICYLENS - CORE SPA FRONTEND LOGIC

document.addEventListener("DOMContentLoaded", () => {
    // -----------------------------------------
    // 1. STATE MANAGEMENT
    // -----------------------------------------
    let sessionId = localStorage.getItem("policylens_session_id");
    if (!sessionId) {
        sessionId = "sess_" + Math.random().toString(36).substring(2, 15);
        localStorage.setItem("policylens_session_id", sessionId);
    }
    
    let activeMode = "benchmark"; // "benchmark" or "session"
    let currentCitations = [];
    let evalPollInterval = null;

    // Obtains display elements
    const sessionDisplay = document.getElementById("session-display");
    if (sessionDisplay) {
        sessionDisplay.textContent = `Session: ${sessionId.substring(5, 12)}...`;
    }

    // -----------------------------------------
    // 2. SPA VIEW NAVIGATION
    // -----------------------------------------
    const navItems = document.querySelectorAll(".nav-item");
    const viewSections = document.querySelectorAll(".view-section");
    const pageTitle = document.getElementById("page-title");
    const sidebar = document.getElementById("app-sidebar");
    const sidebarOpenBtn = document.getElementById("sidebar-open-btn");
    const sidebarCloseBtn = document.getElementById("sidebar-close-btn");

    function navigateToView(viewId) {
        // Toggle view visibility
        viewSections.forEach(section => {
            if (section.id === `view-${viewId}`) {
                section.classList.add("active");
            } else {
                section.classList.remove("active");
            }
        });

        // Toggle active nav class
        navItems.forEach(item => {
            if (item.getAttribute("data-view") === viewId) {
                item.classList.add("active");
            } else {
                item.classList.remove("active");
            }
        });

        // Update page title
        const titles = {
            "dashboard": "Dashboard",
            "benchmark": "Benchmark Mode",
            "try-your-own": "Try Your Own",
            "documents": "Documents Library",
            "evaluation": "Evaluation Bench",
            "settings": "Settings"
        };
        pageTitle.textContent = titles[viewId] || "PolicyLens";
        
        // Hide drawer if open
        closeEvidenceDrawer();

        // View-specific initialization
        if (viewId === "dashboard") {
            loadDashboardStats();
        } else if (viewId === "documents") {
            loadDocumentLibrary();
        } else if (viewId === "settings") {
            loadSettings();
        } else if (viewId === "evaluation") {
            loadEvaluationData();
        } else if (viewId === "try-your-own") {
            activeMode = "session";
            loadSessionDocuments();
        }
        
        if (viewId === "benchmark") {
            activeMode = "benchmark";
        }

        // Close sidebar on mobile
        sidebar.classList.remove("mobile-active");
    }

    navItems.forEach(item => {
        item.addEventListener("click", (e) => {
            e.preventDefault();
            const viewId = item.getAttribute("data-view");
            navigateToView(viewId);
            window.location.hash = viewId;
        });
    });

    // Handle hash links on Mode Cards on Dashboard
    document.querySelectorAll(".mode-card").forEach(card => {
        card.addEventListener("click", () => {
            const target = card.getAttribute("data-target");
            navigateToView(target);
            window.location.hash = target;
        });
    });

    // Mobile Sidebar Toggles
    if (sidebarOpenBtn) {
        sidebarOpenBtn.addEventListener("click", () => sidebar.classList.add("mobile-active"));
    }
    if (sidebarCloseBtn) {
        sidebarCloseBtn.addEventListener("click", () => sidebar.classList.remove("mobile-active"));
    }

    // Direct hash access on load
    if (window.location.hash) {
        const viewHash = window.location.hash.substring(1);
        const validViews = ["dashboard", "benchmark", "try-your-own", "documents", "evaluation", "settings"];
        if (validViews.includes(viewHash)) {
            navigateToView(viewHash);
        }
    } else {
        loadDashboardStats();
    }

    // -----------------------------------------
    // 3. DASHBOARD STATS
    // -----------------------------------------
    function loadDashboardStats() {
        fetch("/api/dashboard/stats")
            .then(res => res.json())
            .then(data => {
                document.getElementById("stat-docs").textContent = data.benchmark_documents;
                document.getElementById("stat-chunks").textContent = data.benchmark_chunks;
                document.getElementById("stat-cases").textContent = data.benchmark_questions;
                
                const statusText = document.getElementById("status-text");
                const statusDot = document.getElementById("status-dot");
                
                if (data.status === "Indexed") {
                    statusText.textContent = "Corpus: Indexed";
                    statusDot.className = "status-dot green";
                } else {
                    statusText.textContent = "Corpus: Not Indexed";
                    statusDot.className = "status-dot yellow";
                }
                
                // Evaluation indicators
                const metrics = data.evaluation_metrics;
                if (metrics) {
                    document.getElementById("stat-hit").textContent = metrics.hit_at_5;
                    document.getElementById("stat-groundedness").textContent = metrics.groundedness;
                    document.getElementById("stat-latency").textContent = metrics.avg_latency;
                } else {
                    document.getElementById("stat-hit").textContent = "--";
                    document.getElementById("stat-groundedness").textContent = "--";
                    document.getElementById("stat-latency").textContent = "--";
                }
            })
            .catch(err => console.error("Error loading stats:", err));
    }

    // -----------------------------------------
    // 4. DOCUMENT LIBRARY
    // -----------------------------------------
    function loadDocumentLibrary() {
        const tableBody = document.getElementById("library-table-body");
        tableBody.innerHTML = `<tr><td colspan="8" class="empty-state">Loading document catalog...</td></tr>`;
        
        fetch(`/api/documents/list?session_id=${sessionId}`)
            .then(res => res.json())
            .then(docs => {
                tableBody.innerHTML = "";
                if (docs.length === 0) {
                    tableBody.innerHTML = `<tr><td colspan="8" class="empty-state">No documents in library.</td></tr>`;
                    return;
                }
                
                docs.forEach(doc => {
                    const tr = document.createElement("tr");
                    
                    let statusClass = "missing";
                    if (doc.status === "Indexed") statusClass = "indexed";
                    else if (doc.status === "Available") statusClass = "available";
                    
                    const scopeText = doc.type === "benchmark" ? "Frozen Benchmark" : "Temporary Session";
                    const actionCell = doc.type === "benchmark" 
                        ? `<a href="/api/documents/download/${doc.document_id}" target="_blank" class="mode-link">Source Act</a>`
                        : `<span class="text-muted">Temporary</span>`;
                        
                    tr.innerHTML = `
                        <td><strong>${doc.title}</strong></td>
                        <td>${doc.category}</td>
                        <td>${doc.source}</td>
                        <td class="font-mono">${doc.pages}</td>
                        <td class="font-mono">${doc.chunks}</td>
                        <td>
                            <div class="status-version-wrapper">
                                <span class="doc-status-badge ${statusClass}">${doc.status}</span>
                                <span class="version-text">${doc.version}</span>
                            </div>
                        </td>
                        <td>${scopeText}</td>
                        <td>${actionCell}</td>
                    `;
                    tableBody.appendChild(tr);
                });
            })
            .catch(err => {
                tableBody.innerHTML = `<tr><td colspan="8" class="empty-state text-danger">Error loading document catalog.</td></tr>`;
                console.error(err);
            });
    }

    // -----------------------------------------
    // 5. SETTINGS
    // -----------------------------------------
    const settingsForm = document.getElementById("settings-form");
    const saveStatusMsg = document.getElementById("save-status-msg");

    function loadSettings() {
        fetch("/api/settings")
            .then(res => res.json())
            .then(data => {
                document.getElementById("set-emb-provider").value = data.embedding_provider;
                document.getElementById("set-llm-provider").value = data.llm_provider;
                document.getElementById("set-chunk-size").value = data.chunk_size;
                document.getElementById("set-chunk-overlap").value = data.chunk_overlap;
                
                document.getElementById("gemini-key-status").textContent = data.gemini_api_key_set ? "✓ Gemini Key Configured" : "✗ Key Not Configured";
                document.getElementById("gemini-key-status").className = data.gemini_api_key_set ? "field-info text-green" : "field-info text-muted";
                
                document.getElementById("openai-key-status").textContent = data.openai_api_key_set ? "✓ OpenAI Key Configured" : "✗ Key Not Configured";
                document.getElementById("openai-key-status").className = data.openai_api_key_set ? "field-info text-green" : "field-info text-muted";
                
                updateSettingsSummary(data.llm_provider, data.models.llm, data.chunk_size);
            })
            .catch(err => console.error("Error loading settings:", err));
    }

    function updateSettingsSummary(provider, model, chunkSize) {
        const text = `LLM: ${provider.toUpperCase()} (${model}) | Size: ${chunkSize} chars`;
        document.getElementById("settings-summary-text").textContent = text;
        const trySummary = document.getElementById("try-settings-summary-text");
        if (trySummary) trySummary.textContent = text;
    }

    if (settingsForm) {
        settingsForm.addEventListener("submit", (e) => {
            e.preventDefault();
            saveStatusMsg.textContent = "Saving...";
            saveStatusMsg.className = "save-status";
            
            const payload = {
                embedding_provider: document.getElementById("set-emb-provider").value,
                llm_provider: document.getElementById("set-llm-provider").value,
                gemini_api_key: document.getElementById("set-gemini-key").value,
                openai_api_key: document.getElementById("set-openai-key").value,
                chunk_size: parseInt(document.getElementById("set-chunk-size").value),
                chunk_overlap: parseInt(document.getElementById("set-chunk-overlap").value)
            };
            
            fetch("/api/settings", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            })
            .then(res => {
                if (!res.ok) throw new Error("Update settings failed.");
                return res.json();
            })
            .then(data => {
                saveStatusMsg.textContent = "Settings saved successfully!";
                saveStatusMsg.className = "save-status success";
                
                // Clear password inputs
                document.getElementById("set-gemini-key").value = "";
                document.getElementById("set-openai-key").value = "";
                
                // Reload settings details
                loadSettings();
                loadDashboardStats();
                
                setTimeout(() => {
                    saveStatusMsg.textContent = "";
                }, 4000);
            })
            .catch(err => {
                saveStatusMsg.textContent = "Error saving configuration.";
                saveStatusMsg.className = "save-status error";
                console.error(err);
            });
        });
    }

    // -----------------------------------------
    // 6. PIPELINE CHAT / ASK LOGIC
    // -----------------------------------------
    const queryInput = document.getElementById("query-input");
    const askBtn = document.getElementById("ask-btn");
    
    const tryQueryInput = document.getElementById("try-query-input");
    const tryAskBtn = document.getElementById("try-ask-btn");

    function executeQuery(question, mode) {
        const isBenchmark = mode === "benchmark";
        
        // Target elements
        const inputEl = isBenchmark ? queryInput : tryQueryInput;
        const btnEl = isBenchmark ? askBtn : tryAskBtn;
        const statusCard = document.getElementById(isBenchmark ? "pipeline-status-card" : "try-pipeline-status-card");
        const answerCard = document.getElementById(isBenchmark ? "answer-container" : "try-answer-container");
        
        // Step bullets
        const stepInit = document.getElementById(isBenchmark ? "step-init" : "try-step-init");
        const stepEmbed = document.getElementById(isBenchmark ? "step-embed" : "try-step-embed");
        const stepRetrieval = document.getElementById(isBenchmark ? "step-retrieval" : "try-step-retrieval");
        const stepLLM = document.getElementById(isBenchmark ? "step-llm" : "try-step-llm");

        // Clear output views
        answerCard.classList.add("hidden");
        statusCard.classList.remove("hidden");
        btnEl.disabled = true;
        
        // Reset steps UI helper
        const steps = isBenchmark 
            ? ["step-init", "step-embed", "step-retrieval", "step-llm"]
            : ["try-step-init", "try-step-embed", "try-step-retrieval", "try-step-llm"];
            
        steps.forEach(s => {
            const el = document.getElementById(s);
            if (el) {
                el.className = "log-step";
                el.querySelector(".step-time").textContent = "--";
            }
        });

        // Set Step 1: Active
        setStepState(steps[0], "running");
        
        const payload = {
            question: question,
            mode: isBenchmark ? "benchmark" : `sessions/${sessionId}`,
            top_k: 5
        };

        const t0 = performance.now();
        
        // Simple timing animations if backend runs fast
        setTimeout(() => setStepState(steps[0], "completed", 0.05), 100);
        setTimeout(() => setStepState(steps[1], "running"), 150);

        fetch("/api/chat/ask", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        })
        .then(res => {
            if (!res.ok) throw new Error("API call returned failure status.");
            return res.json();
        })
        .then(data => {
            // Render operations details
            const pSteps = data.pipeline_steps || {};
            
            setStepState(steps[1], "completed", pSteps.embedding || 0.12);
            setStepState(steps[2], "running");
            
            setTimeout(() => {
                setStepState(steps[2], "completed", pSteps.retrieval || 0.05);
                setStepState(steps[3], "running");
                
                setTimeout(() => {
                    setStepState(steps[3], "completed", pSteps.generation || 1.84);
                    
                    // Render Answer
                    setTimeout(() => {
                        statusCard.classList.add("hidden");
                        renderAnswer(data, isBenchmark);
                        btnEl.disabled = false;
                    }, 300);
                    
                }, 400);
            }, 300);
        })
        .catch(err => {
            statusCard.classList.add("hidden");
            btnEl.disabled = false;
            
            // Show error in Answer container
            answerCard.classList.remove("hidden");
            const answerBody = document.getElementById(isBenchmark ? "answer-text" : "try-answer-text");
            answerBody.innerHTML = `<p class="text-danger"><strong>Error:</strong> Failed to fetch answer from PolicyLens API. Please verify that your LLM API Keys are correctly set up in the Settings tab.</p>`;
            
            const badge = document.getElementById(isBenchmark ? "evidence-status-badge" : "try-evidence-status-badge");
            badge.className = "evidence-badge insufficient";
            const label = document.getElementById(isBenchmark ? "evidence-status-label" : "try-evidence-status-label");
            label.textContent = "Error";
            
            console.error(err);
        });
    }

    function setStepState(elementId, state, duration = null) {
        const el = document.getElementById(elementId);
        if (!el) return;
        
        el.className = `log-step ${state}`;
        if (duration !== null) {
            el.querySelector(".step-time").textContent = `${duration.toFixed(2)}s`;
        }
    }

    function renderAnswer(data, isBenchmark) {
        const prefix = isBenchmark ? "" : "try-";
        
        const container = document.getElementById(`${prefix}answer-container`);
        const textEl = document.getElementById(`${prefix}answer-text`);
        const badgeEl = document.getElementById(`${prefix}evidence-status-badge`);
        const labelEl = document.getElementById(`${prefix}evidence-status-label`);
        const latencyEl = document.getElementById(`${prefix}meta-latency`);
        const costEl = document.getElementById(`${prefix}meta-cost`);
        const gridEl = document.getElementById(`${prefix}citations-grid`);
        const conflictEl = document.getElementById("conflict-warning");

        // Parse markdown text using marked.js if available, else standard fallback
        let parsedHtml = "";
        if (typeof marked !== "undefined" && marked.parse) {
            parsedHtml = marked.parse(data.answer);
        } else {
            parsedHtml = `<p>${data.answer.replace(/\n\n/g, "</p><p>").replace(/\n/g, "<br>")}</p>`;
        }
        
        // Post-process HTML to turn citation markers e.g. [1], [2] into interactive link tags
        parsedHtml = parsedHtml.replace(/\[(\d+)\]/g, (match, num) => {
            return `<a class="citation-link" data-citation-id="${num}">[${num}]</a>`;
        });
        
        textEl.innerHTML = parsedHtml;
        
        // Hook up event listeners to inline citation links
        textEl.querySelectorAll(".citation-link").forEach(link => {
            link.addEventListener("click", () => {
                const citationId = parseInt(link.getAttribute("data-citation-id"));
                openEvidenceDrawer(citationId);
            });
        });

        // Set evidence strength badge
        badgeEl.className = `evidence-badge ${data.evidence_status}`;
        
        const labels = {
            "strong": "✓ Strong Evidence",
            "limited": "⚠ Limited Evidence",
            "insufficient": "! Insufficient Evidence"
        };
        labelEl.textContent = labels[data.evidence_status] || data.evidence_status;

        // Conflict warning
        if (conflictEl) {
            if (data.conflict_detected) {
                conflictEl.classList.remove("hidden");
            } else {
                conflictEl.classList.add("hidden");
            }
        }

        // Meta info
        latencyEl.textContent = `Latency: ${data.latency.toFixed(2)}s`;
        costEl.textContent = `Cost: $${data.cost.toFixed(6)}`;

        // Citations List
        gridEl.innerHTML = "";
        currentCitations = data.citations || [];
        
        if (currentCitations.length === 0) {
            gridEl.innerHTML = `<span class="text-muted">No citations available.</span>`;
        } else {
            currentCitations.forEach(citation => {
                const card = document.createElement("div");
                card.className = "citation-card";
                card.innerHTML = `
                    <div class="citation-card-header">
                        <span class="citation-num-badge">${citation.id}</span>
                        <span class="citation-doc-title">${citation.document_title}</span>
                    </div>
                    <div class="citation-card-meta">
                        <span>${citation.section || "General"}</span>
                        <span>Page ${citation.page}</span>
                    </div>
                    <span class="citation-expand-action">View Evidence Passage →</span>
                `;
                
                card.addEventListener("click", () => {
                    openEvidenceDrawer(citation.id);
                });
                gridEl.appendChild(card);
            });
        }

        container.classList.remove("hidden");
        
        // Scroll to answer smoothly
        container.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }

    if (askBtn) {
        askBtn.addEventListener("click", () => {
            const question = queryInput.value.strip ? queryInput.value.strip() : queryInput.value.trim();
            if (question) executeQuery(question, "benchmark");
        });
    }

    if (tryAskBtn) {
        tryAskBtn.addEventListener("click", () => {
            const question = tryQueryInput.value.strip ? tryQueryInput.value.strip() : tryQueryInput.value.trim();
            if (question) executeQuery(question, "session");
        });
    }

    // Suggest Question button
    const suggestBtn = document.getElementById("suggest-q-btn");
    if (suggestBtn) {
        suggestBtn.addEventListener("click", () => {
            const suggestions = [
                "What fundamental rights are protected under Article 25 of the Constitution of Pakistan?",
                "What constitutes the offense of cyber terrorism and what is its penalty under PECA?",
                "What is the punishment for theft under Section 379 of the Pakistan Penal Code?",
                "What information is exempted from public disclosure under the Right of Access to Information Act?",
                "What is the principle of Res Judicata under Section 11 of the CPC?"
            ];
            const randomQ = suggestions[Math.floor(Math.random() * suggestions.length)];
            queryInput.value = randomQ;
            queryInput.focus();
        });
    }

    // Helper step status templates for Try-Your-Own
    const tryLogSteps = document.getElementById("try-log-steps");
    if (tryLogSteps) {
        tryLogSteps.innerHTML = `
            <div class="log-step" id="try-step-init">
                <span class="step-bullet"></span>
                <span class="step-label">Initializing session index...</span>
                <span class="step-time">--</span>
            </div>
            <div class="log-step" id="try-step-embed">
                <span class="step-bullet"></span>
                <span class="step-label">Embedding query vector...</span>
                <span class="step-time">--</span>
            </div>
            <div class="log-step" id="try-step-retrieval">
                <span class="step-bullet"></span>
                <span class="step-label">Searching custom files...</span>
                <span class="step-time">--</span>
            </div>
            <div class="log-step" id="try-step-llm">
                <span class="step-bullet"></span>
                <span class="step-label">Generating grounded answer...</span>
                <span class="step-time">--</span>
            </div>
        `;
    }

    // -----------------------------------------
    // 7. EVIDENCE DRAWER (Verification)
    // -----------------------------------------
    const drawer = document.getElementById("evidence-drawer");
    const drawerOverlay = document.getElementById("drawer-overlay");
    const drawerCloseBtn = document.getElementById("drawer-close-btn");
    
    function openEvidenceDrawer(citationId) {
        const citation = currentCitations.find(c => c.id === citationId);
        if (!citation) return;

        document.getElementById("drawer-doc").textContent = citation.document_title;
        document.getElementById("drawer-section").textContent = citation.section || "General/Unspecified";
        document.getElementById("drawer-page").textContent = `Page ${citation.page}`;
        document.getElementById("drawer-text").textContent = citation.text;
        
        // Clean technical metadata for inspection
        const cleanedMetadata = {
            chunk_id: citation.metadata.chunk_id,
            document_id: citation.document_id,
            version: citation.metadata.version,
            source: citation.metadata.source,
            source_url: citation.metadata.source_url
        };
        document.getElementById("drawer-metadata").textContent = JSON.stringify(cleanedMetadata, null, 2);

        drawer.classList.add("active");
        drawerOverlay.classList.add("active");
    }

    function closeEvidenceDrawer() {
        drawer.classList.remove("active");
        drawerOverlay.classList.remove("active");
    }

    if (drawerCloseBtn) drawerCloseBtn.addEventListener("click", closeEvidenceDrawer);
    if (drawerOverlay) drawerOverlay.addEventListener("click", closeEvidenceDrawer);

    // -----------------------------------------
    // 8. TRY YOUR OWN: PDF UPLOAD WORKFLOW
    // -----------------------------------------
    const dropzone = document.getElementById("upload-dropzone");
    const fileInput = document.getElementById("upload-file-input");
    const progressBox = document.getElementById("upload-progress-box");
    const progressFill = document.getElementById("upload-progress-fill");
    const progressFilename = document.getElementById("upload-filename-text");
    const progressSteps = document.getElementById("upload-progress-steps");
    const clearSessionBtn = document.getElementById("clear-session-btn");

    function loadSessionDocuments() {
        const docsList = document.getElementById("session-docs-list");
        const placeholder = document.getElementById("upload-chat-placeholder");
        const chatWorkspace = document.getElementById("upload-chat-active");

        fetch(`/api/documents/list?session_id=${sessionId}`)
            .then(res => res.json())
            .then(docs => {
                const sessionDocs = docs.filter(d => d.type === "session");
                docsList.innerHTML = "";
                
                if (sessionDocs.length === 0) {
                    docsList.innerHTML = `<div class="empty-state">No custom files uploaded yet.</div>`;
                    placeholder.classList.remove("hidden");
                    chatWorkspace.classList.add("hidden");
                } else {
                    placeholder.classList.add("hidden");
                    chatWorkspace.classList.remove("hidden");
                    
                    sessionDocs.forEach(doc => {
                        const item = document.createElement("div");
                        item.className = "session-doc-item";
                        item.innerHTML = `
                            <div class="session-doc-icon">
                                <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>
                            </div>
                            <div class="session-doc-details">
                                <span class="session-doc-name" title="${doc.title}">${doc.title}</span>
                                <span class="session-doc-meta">${doc.chunks} chunks | Pages: ${doc.pages}</span>
                            </div>
                        `;
                        docsList.appendChild(item);
                    });
                }
            })
            .catch(err => console.error("Error loading session docs:", err));
    }

    if (dropzone) {
        dropzone.addEventListener("click", () => fileInput.click());
        
        dropzone.addEventListener("dragover", (e) => {
            e.preventDefault();
            dropzone.classList.add("dragover");
        });
        
        dropzone.addEventListener("dragleave", () => {
            dropzone.classList.remove("dragover");
        });
        
        dropzone.addEventListener("drop", (e) => {
            e.preventDefault();
            dropzone.classList.remove("dragover");
            const files = e.dataTransfer.files;
            if (files.length > 0) uploadPDFs(files);
        });
    }

    if (fileInput) {
        fileInput.addEventListener("change", (e) => {
            const files = e.target.files;
            if (files.length > 0) uploadPDFs(files);
        });
    }

    function uploadPDFs(files) {
        const formData = new FormData();
        let validPDFsCount = 0;
        
        for (let i = 0; i < files.length; i++) {
            if (files[i].name.toLowerCase().endsWith(".pdf")) {
                formData.append("files", files[i]);
                validPDFsCount++;
            }
        }
        
        if (validPDFsCount === 0) {
            alert("Please select valid PDF documents.");
            return;
        }

        formData.append("session_id", sessionId);
        
        progressFilename.textContent = files.length === 1 ? files[0].name : `${validPDFsCount} PDF files...`;
        progressBox.classList.remove("hidden");
        progressFill.style.width = "10%";
        progressSteps.innerHTML = `<span class="active">Uploading</span> → <span>Extracting</span> → <span>Indexing</span>`;

        // Simulate progresses
        setTimeout(() => {
            progressFill.style.width = "40%";
            progressSteps.innerHTML = `<span>Uploading</span> → <span class="active">Extracting text</span> → <span>Indexing</span>`;
        }, 800);

        fetch("/api/documents/upload", {
            method: "POST",
            body: formData
        })
        .then(res => {
            if (!res.ok) throw new Error("Upload failed");
            return res.json();
        })
        .then(data => {
            progressFill.style.width = "100%";
            progressSteps.innerHTML = `<span>Uploading</span> → <span>Extracting</span> → <span class="active">Ready!</span>`;
            
            setTimeout(() => {
                progressBox.classList.add("hidden");
                loadSessionDocuments();
                loadDashboardStats();
            }, 1000);
        })
        .catch(err => {
            progressBox.classList.add("hidden");
            alert("Error uploading or indexing PDFs. Please make sure that your LLM API Keys are correctly set in the Settings tab.");
            console.error(err);
        });
    }

    if (clearSessionBtn) {
        clearSessionBtn.addEventListener("click", () => {
            if (!confirm("Are you sure you want to clear all uploaded session files?")) return;
            
            const formData = new FormData();
            formData.append("session_id", sessionId);
            
            fetch("/api/documents/clear-session", {
                method: "POST",
                body: formData
            })
            .then(res => res.json())
            .then(data => {
                loadSessionDocuments();
                loadDashboardStats();
                
                // Hide chats
                document.getElementById("try-answer-container").classList.add("hidden");
                document.getElementById("try-pipeline-status-card").classList.add("hidden");
            })
            .catch(err => console.error("Error clearing session:", err));
        });
    }

    // -----------------------------------------
    // 9. EVALUATION CONSOLE & DETAILS
    // -----------------------------------------
    const runEvalBtn = document.getElementById("run-eval-btn");
    const evalProgressBox = document.getElementById("eval-progress-box");
    const evalPlaceholder = document.getElementById("eval-placeholder");
    const evalDashboard = document.getElementById("eval-dashboard-active");
    const evalErrorBanner = document.getElementById("eval-error-banner");

    function loadEvaluationData() {
        fetch("/api/evaluation/results")
            .then(res => {
                if (res.status === 404) {
                    evalPlaceholder.classList.remove("hidden");
                    evalDashboard.classList.add("hidden");
                    throw new Error("Evaluation not run yet");
                }
                if (!res.ok) throw new Error("Failed to load eval details");
                return res.json();
            })
            .then(data => {
                evalPlaceholder.classList.add("hidden");
                evalDashboard.classList.remove("hidden");
                
                // Render stats
                const results = data.results || [];
                if (results.length > 0) {
                    const total = results.length;
                    const hit = results.reduce((acc, r) => acc + r.hit_at_5, 0) / total;
                    const ground = results.reduce((acc, r) => acc + r.groundedness, 0) / total;
                    const cit = results.reduce((acc, r) => acc + r.citation_accuracy, 0) / total;
                    const relevance = results.reduce((acc, r) => acc + r.relevance, 0) / total;
                    const latencies = results.map(r => r.latency);
                    const avgLatency = latencies.reduce((acc, l) => acc + l, 0) / total;
                    
                    document.getElementById("eval-stat-count").textContent = total;
                    document.getElementById("eval-stat-hit").textContent = `${(hit * 100).toFixed(1)}%`;
                    document.getElementById("eval-stat-ground").textContent = `${(ground * 100).toFixed(1)}%`;
                    document.getElementById("eval-stat-cit").textContent = `${(cit * 100).toFixed(1)}%`;
                    document.getElementById("eval-stat-rel").textContent = `${(relevance * 100).toFixed(1)}%`;
                    document.getElementById("eval-stat-latency").textContent = `${avgLatency.toFixed(2)}s`;
                }

                // Render Markdown reports
                if (typeof marked !== "undefined" && marked.parse) {
                    document.getElementById("eval-report-markdown").innerHTML = marked.parse(data.report_md || "No report generated.");
                    document.getElementById("eval-failures-markdown").innerHTML = marked.parse(data.failure_md || "No failures generated.");
                } else {
                    document.getElementById("eval-report-markdown").innerHTML = `<pre>${data.report_md}</pre>`;
                    document.getElementById("eval-failures-markdown").innerHTML = `<pre>${data.failure_md}</pre>`;
                }

                // Render Detailed Table rows
                const tableBody = document.getElementById("eval-table-body");
                tableBody.innerHTML = "";
                
                results.forEach(r => {
                    const tr = document.createElement("tr");
                    const statusIcon = r.hit_at_5 > 0.9 && r.groundedness > 0.8 ? "✓ Passed" : "⚠ Review";
                    const statusClass = r.hit_at_5 > 0.9 && r.groundedness > 0.8 ? "text-green" : "text-warning";
                    
                    tr.innerHTML = `
                        <td><strong>${r.id}</strong></td>
                        <td title="${r.question}">${r.question.substring(0, 50)}...</td>
                        <td>${r.type}</td>
                        <td>${(r.hit_at_5 * 100).toFixed(0)}%</td>
                        <td>${(r.groundedness * 100).toFixed(0)}%</td>
                        <td>${(r.citation_accuracy * 100).toFixed(0)}%</td>
                        <td>${r.latency.toFixed(2)}s</td>
                        <td>$${r.cost.toFixed(5)}</td>
                        <td class="${statusClass}"><strong>${statusIcon}</strong></td>
                    `;
                    tableBody.appendChild(tr);
                });
            })
            .catch(err => {
                // Silently handle placeholder states
                console.log(err.message);
            });
    }

    if (runEvalBtn) {
        runEvalBtn.addEventListener("click", () => {
            if (confirm("Run evaluation harness now? This runs all 20 test cases and may consume API tokens if configured. Confirm to proceed.")) {
                runEvalBtn.disabled = true;
                evalProgressBox.classList.remove("hidden");
                evalErrorBanner.classList.add("hidden");
                
                fetch("/api/evaluation/run", { method: "POST" })
                    .then(res => res.json())
                    .then(data => {
                        // Start polling
                        pollEvaluationStatus();
                    })
                    .catch(err => {
                        runEvalBtn.disabled = false;
                        evalProgressBox.classList.add("hidden");
                        alert("Failed to start evaluation.");
                        console.error(err);
                    });
            }
        });
    }

    function pollEvaluationStatus() {
        if (evalPollInterval) clearInterval(evalPollInterval);
        
        evalPollInterval = setInterval(() => {
            fetch("/api/evaluation/status")
                .then(res => res.json())
                .then(status => {
                    if (!status.is_running) {
                        clearInterval(evalPollInterval);
                        runEvalBtn.disabled = false;
                        evalProgressBox.classList.add("hidden");
                        
                        if (status.error) {
                            evalErrorBanner.textContent = `Evaluation failed: ${status.error}`;
                            evalErrorBanner.classList.remove("hidden");
                        } else {
                            loadEvaluationData();
                            loadDashboardStats();
                        }
                    }
                })
                .catch(err => {
                    clearInterval(evalPollInterval);
                    runEvalBtn.disabled = false;
                    evalProgressBox.classList.add("hidden");
                    console.error("Error polling status:", err);
                });
        }, 2000);
    }

    // Hook up Evaluation tab toggles
    document.querySelectorAll(".eval-tab").forEach(tab => {
        tab.addEventListener("click", () => {
            // Deactivate other tabs
            document.querySelectorAll(".eval-tab").forEach(t => t.classList.remove("active"));
            document.querySelectorAll(".eval-tab-content").forEach(c => c.classList.remove("active"));
            
            // Activate clicked
            tab.classList.add("active");
            const targetId = tab.getAttribute("data-target");
            document.getElementById(targetId).classList.add("active");
        });
    });
});
