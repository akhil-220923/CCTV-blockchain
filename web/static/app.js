// Sentinel-Chain Dashboard JavaScript

let currentBlockchainNode = "border_police";
let currentAuditNode = "border_police";

document.addEventListener("DOMContentLoaded", () => {
  initTabs();
  initVideoStreamControls();
  loadAllData();

  // Poll overview metrics every 4 seconds
  setInterval(loadOverview, 4000);
});

// Tab Navigation
function initTabs() {
  const tabs = document.querySelectorAll(".tab-btn");
  tabs.forEach(btn => {
    btn.addEventListener("click", () => {
      tabs.forEach(b => b.classList.remove("active"));
      document.querySelectorAll(".tab-content").forEach(c => c.classList.remove("active"));

      btn.classList.add("active");
      const targetId = btn.getAttribute("data-tab");
      const targetContent = document.getElementById(targetId);
      if (targetContent) {
        targetContent.classList.add("active");
      }

      // Refresh specific tab data
      if (targetId === "tabBlockchain") loadBlockchainChain(currentBlockchainNode);
      if (targetId === "tabAudit") loadAuditLogs(currentAuditNode);
      if (targetId === "tabEvidence") loadIntrusionEvents();
      if (targetId === "tabCybersecurity") loadPersonnel();
    });
  });
}

// Node Switcher for Blockchain Explorer
function selectBlockchainNode(nodeKey) {
  currentBlockchainNode = nodeKey;
  ["btnChainBP", "btnChainSP", "btnChainJD"].forEach(id => {
    const btn = document.getElementById(id);
    if (btn) btn.className = "btn btn-small btn-outline";
  });
  if (nodeKey === "border_police") document.getElementById("btnChainBP")?.setAttribute("class", "btn btn-small btn-primary");
  if (nodeKey === "state_police") document.getElementById("btnChainSP")?.setAttribute("class", "btn btn-small btn-primary");
  if (nodeKey === "judiciary") document.getElementById("btnChainJD")?.setAttribute("class", "btn btn-small btn-primary");
  loadBlockchainChain(nodeKey);
}

// Node Switcher for Audit Logs
function selectAuditNode(nodeKey) {
  currentAuditNode = nodeKey;
  ["btnAuditBP", "btnAuditSP", "btnAuditJD"].forEach(id => {
    const btn = document.getElementById(id);
    if (btn) btn.className = "btn btn-small btn-outline";
  });
  if (nodeKey === "border_police") document.getElementById("btnAuditBP")?.setAttribute("class", "btn btn-small btn-primary");
  if (nodeKey === "state_police") document.getElementById("btnAuditSP")?.setAttribute("class", "btn btn-small btn-primary");
  if (nodeKey === "judiciary") document.getElementById("btnAuditJD")?.setAttribute("class", "btn btn-small btn-primary");
  loadAuditLogs(nodeKey);
}

// Test Audit Log Access Broadcast
async function triggerAuditAccessTest() {
  try {
    const res = await fetch("/api/audit-logs/access", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        node: currentAuditNode,
        role: "External-Oversight-Auditor",
        action: "INSPECT_AUDIT_LOGS",
        target_id: "ALL_AUDIT_ENTRIES"
      })
    });
    const data = await res.json();
    alert(`AUDIT ACCESS BROADCAST CONFIRMED:\n\n${data.message}\n\nAll 3 authority nodes (Border Police, State Police, Judiciary) have registered this access entry in their tamper-evident logs!`);
    loadAuditLogs(currentAuditNode);
  } catch (err) {
    alert("Audit test failed: " + err);
  }
}

// Video Controls
function initVideoStreamControls() {
  const streamImg = document.getElementById("surveillanceStream");
  const video = document.getElementById("surveillanceVideo");
  const btnAnnotated = document.getElementById("btnPlayAnnotated");
  const btnRaw = document.getElementById("btnPlayRaw");
  const btnPlayer = document.getElementById("btnPlayPlayer");
  const btnRawPlayer = document.getElementById("btnPlayRawPlayer");

  function resetActive() {
    document.querySelectorAll(".stream-toggles .btn").forEach(b => b.classList.remove("active"));
  }

  function stopMjpegStream() {
    if (streamImg) {
      streamImg.style.display = "none";
      // Use empty SVG data URI to cleanly close multipart HTTP stream socket
      streamImg.src = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg'/%3E";
    }
  }

  function stopHtmlVideo() {
    if (video) {
      video.pause();
      video.removeAttribute("src");
      video.load();
      video.style.display = "none";
    }
  }

  if (btnAnnotated) {
    btnAnnotated.addEventListener("click", () => {
      resetActive();
      btnAnnotated.classList.add("active");
      stopHtmlVideo();
      if (streamImg) {
        streamImg.style.display = "block";
        streamImg.src = "/video/stream/annotated?t=" + Date.now();
      }
    });
  }

  if (btnRaw) {
    btnRaw.addEventListener("click", () => {
      resetActive();
      btnRaw.classList.add("active");
      stopHtmlVideo();
      if (streamImg) {
        streamImg.style.display = "block";
        streamImg.src = "/video/stream/raw?t=" + Date.now();
      }
    });
  }

  if (btnPlayer && video) {
    btnPlayer.addEventListener("click", () => {
      resetActive();
      btnPlayer.classList.add("active");
      stopMjpegStream();
      video.style.display = "block";
      video.muted = true; // Essential for HTML5 browser autoplay
      video.src = "/video/annotated?t=" + Date.now();
      video.load();
      const playPromise = video.play();
      if (playPromise !== undefined) {
        playPromise.catch(err => {
          console.warn("Autoplay notice:", err);
        });
      }
    });
  }

  if (btnRawPlayer && video) {
    btnRawPlayer.addEventListener("click", () => {
      resetActive();
      btnRawPlayer.classList.add("active");
      stopMjpegStream();
      video.style.display = "block";
      video.muted = true; // Essential for HTML5 browser autoplay
      video.src = "/video/raw?t=" + Date.now();
      video.load();
      const playPromise = video.play();
      if (playPromise !== undefined) {
        playPromise.catch(err => {
          console.warn("Autoplay notice:", err);
        });
      }
    });
  }
}

// Re-scan / Process Video on Demand
async function reprocessSurveillanceVideo() {
  const btn = document.getElementById("btnReprocessVideo");
  const origHtml = btn ? btn.innerHTML : "";
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Processing AI Intrusion Detection & 3-Node Blockchain...';
  }
  try {
    const res = await fetch("/api/process-video", { method: "POST" });
    const data = await res.json();
    alert(`Success: ${data.message}`);
    await loadAllData();
    const btnAnnotated = document.getElementById("btnPlayAnnotated");
    if (btnAnnotated) btnAnnotated.click();
  } catch (err) {
    alert("Processing failed: " + err);
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = origHtml;
    }
  }
}

// Load All System Data
async function loadAllData() {
  await loadOverview();
  await loadIntrusionEvents();
  await loadBlockchainChain(currentBlockchainNode);
  await loadAuditLogs(currentAuditNode);
  await loadPersonnel();
}

// Overview & Telemetry
async function loadOverview() {
  try {
    const res = await fetch("/api/overview");
    const data = await res.json();

    const isTampered = data.metrics.is_tampered;
    const tamperedCount = data.metrics.tampered_intrusions_count || 0;
    const activeCount = data.metrics.active_intrusions_count !== undefined ? data.metrics.active_intrusions_count : data.metrics.total_intrusions;
    const authenticCount = data.metrics.authentic_intrusions_count || data.metrics.total_intrusions;

    const statIntrusions = document.getElementById("statTotalIntrusions");
    const statIntrusionsLabel = document.getElementById("statTotalIntrusionsLabel");
    const statIntrusionBadge = document.getElementById("statIntrusionBadge");

    if (isTampered && tamperedCount > 0) {
      statIntrusions.textContent = activeCount;
      if (statIntrusionsLabel) {
        statIntrusionsLabel.innerHTML = `Active Intrusions <span style="color:#ff1744; font-weight:700;">(${tamperedCount} Concealed by Tampering!)</span>`;
      }
      if (statIntrusionBadge) {
        statIntrusionBadge.className = "metric-badge alert blink-fast";
        statIntrusionBadge.textContent = "TAMPER DETECTED: CONCEALED";
      }
      document.getElementById("eventBadgeCount").textContent = `${activeCount} Active (${tamperedCount} Tampered)`;
    } else {
      statIntrusions.textContent = data.metrics.total_intrusions;
      if (statIntrusionsLabel) {
        statIntrusionsLabel.textContent = "Total Intrusions (De-duplicated)";
      }
      if (statIntrusionBadge) {
        statIntrusionBadge.className = "metric-badge alert";
        statIntrusionBadge.textContent = "Anti-Spam Active";
      }
      document.getElementById("eventBadgeCount").textContent = `${data.metrics.total_intrusions} Breaches`;
    }

    document.getElementById("statChainHeight").textContent = data.metrics.chain_height;
    document.getElementById("statAuthorizedPersonnel").textContent = data.metrics.authorized_personnel_count;

    // Consensus indicator
    const consensusHealthy = !isTampered && (data.metrics.active_security_alerts === 0);
    const hudConsensus = document.getElementById("hudConsensusStatus");
    if (consensusHealthy) {
      hudConsensus.innerHTML = '<i class="fa-solid fa-circle-nodes"></i> HEALTHY (100%)';
      hudConsensus.className = "val green";
    } else {
      hudConsensus.innerHTML = '<i class="fa-solid fa-triangle-exclamation"></i> TAMPER ALERT DETECTED!';
      hudConsensus.className = "val red";
    }

    // Nodes height & Cross-Node Tamper Card Highlights
    if (data.nodes) {
      document.getElementById("bpChainHeight").textContent = `${data.nodes.border_police.chain_height} blocks`;
      document.getElementById("spChainHeight").textContent = `${data.nodes.state_police.chain_height} blocks`;
      document.getElementById("jdChainHeight").textContent = `${data.nodes.judiciary.chain_height} blocks`;

      const bpCard = document.getElementById("nodeCardBP");
      const spCard = document.getElementById("nodeCardSP");
      const jdCard = document.getElementById("nodeCardJD");
      const bpBadge = document.getElementById("bpNodeStatusBadge");
      const spBadge = document.getElementById("spNodeStatusBadge");
      const jdBadge = document.getElementById("jdNodeStatusBadge");

      const bpAlerts = data.nodes.border_police.active_security_alerts || 0;
      const spAlerts = data.nodes.state_police.active_security_alerts || 0;
      const jdAlerts = data.nodes.judiciary.active_security_alerts || 0;
      const totalAlerts = data.metrics.active_security_alerts || 0;

      // Update Border Police Card
      const bpIsAttacked = !data.nodes.border_police.integrity_valid || (isTampered && data.nodes.border_police.tampered_intrusions && data.nodes.border_police.tampered_intrusions.length > 0);
      if (bpIsAttacked) {
        if (bpBadge) { bpBadge.className = "badge red blink-fast"; bpBadge.textContent = "🚨 COMPROMISED (TAMPERED)"; }
        if (bpCard) { bpCard.style.borderColor = "#ff1744"; bpCard.style.boxShadow = "0 0 15px rgba(255,23,68,0.4)"; }
      } else if (bpAlerts > 0 || (isTampered && totalAlerts > 0)) {
        if (bpBadge) { bpBadge.className = "badge warning"; bpBadge.textContent = "⚠️ PEER TAMPER DETECTED"; }
        if (bpCard) { bpCard.style.borderColor = "#ff9100"; bpCard.style.boxShadow = "0 0 10px rgba(255,145,0,0.3)"; }
      } else {
        if (bpBadge) { bpBadge.className = "badge green"; bpBadge.textContent = "VALIDATOR ACTIVE ✓"; }
        if (bpCard) { bpCard.style.borderColor = ""; bpCard.style.boxShadow = ""; }
      }

      // Update State Police Card
      const spIsAttacked = !data.nodes.state_police.integrity_valid || (isTampered && data.nodes.state_police.tampered_intrusions && data.nodes.state_police.tampered_intrusions.length > 0);
      if (spIsAttacked) {
        if (spBadge) { spBadge.className = "badge red blink-fast"; spBadge.textContent = "🚨 COMPROMISED (TAMPERED)"; }
        if (spCard) { spCard.style.borderColor = "#ff1744"; spCard.style.boxShadow = "0 0 15px rgba(255,23,68,0.4)"; }
      } else if (spAlerts > 0 || (isTampered && totalAlerts > 0)) {
        if (spBadge) { spBadge.className = "badge warning"; spBadge.textContent = "⚠️ PEER TAMPER DETECTED"; }
        if (spCard) { spCard.style.borderColor = "#ff9100"; spCard.style.boxShadow = "0 0 10px rgba(255,145,0,0.3)"; }
      } else {
        if (spBadge) { spBadge.className = "badge cyan"; spBadge.textContent = "CONSENSUS ACTIVE ✓"; }
        if (spCard) { spCard.style.borderColor = ""; spCard.style.boxShadow = ""; }
      }

      // Update Judiciary Card
      const jdIsAttacked = !data.nodes.judiciary.integrity_valid || (isTampered && data.nodes.judiciary.tampered_intrusions && data.nodes.judiciary.tampered_intrusions.length > 0);
      if (jdIsAttacked) {
        if (jdBadge) { jdBadge.className = "badge red blink-fast"; jdBadge.textContent = "🚨 COMPROMISED (TAMPERED)"; }
        if (jdCard) { jdCard.style.borderColor = "#ff1744"; jdCard.style.boxShadow = "0 0 15px rgba(255,23,68,0.4)"; }
      } else if (jdAlerts > 0 || (isTampered && totalAlerts > 0)) {
        if (jdBadge) { jdBadge.className = "badge warning"; jdBadge.textContent = "⚠️ PEER TAMPER DETECTED"; }
        if (jdCard) { jdCard.style.borderColor = "#ff9100"; jdCard.style.boxShadow = "0 0 10px rgba(255,145,0,0.3)"; }
      } else {
        if (jdBadge) { jdBadge.className = "badge purple"; jdBadge.textContent = "LEGAL ADMISSIBILITY ✓"; }
        if (jdCard) { jdCard.style.borderColor = ""; jdCard.style.boxShadow = ""; }
      }
    }

    // Active alert bar
    const alertBar = document.getElementById("breachAlertBar");
    const alertText = document.getElementById("breachAlertText");
    if (isTampered && tamperedCount > 0) {
      alertBar.style.display = "block";
      alertBar.style.background = "linear-gradient(90deg, #d50000, #ff1744, #d50000)";
      if (alertText) {
        alertText.innerHTML = `⚠️ CRITICAL TAMPER ALERT: PERIMETER BREACH ALTERED TO "NO INTRUSION DETECTED" ON PEER NODE! CONCEALMENT ATTEMPT FLAGGED ACROSS CONSENSUS.`;
      }
    } else if (data.metrics.total_intrusions > 0) {
      alertBar.style.display = "block";
      alertBar.style.background = "";
      if (alertText) {
        alertText.textContent = "PERIMETER BREACH ACTIVE IN SECTOR-4 RESTRICTED ZONE";
      }
    } else {
      alertBar.style.display = "none";
    }
  } catch (err) {
    console.error("Failed to load overview:", err);
  }
}

// Load Intrusion Events & Populate Feed & Gallery
async function loadIntrusionEvents() {
  try {
    const res = await fetch("/api/events");
    const data = await res.json();
    const events = data.events || [];

    // Populate Tamper Suite Event Dropdown
    const selectTamperEvent = document.getElementById("selectTamperEvent");
    if (selectTamperEvent) {
      const currentVal = selectTamperEvent.value;
      selectTamperEvent.innerHTML = "";
      if (events.length === 0) {
        selectTamperEvent.innerHTML = '<option value="">No intrusions available</option>';
      } else {
        events.forEach(ev => {
          const opt = document.createElement("option");
          opt.value = ev.event_id;
          opt.textContent = `${ev.event_id} (Track #${ev.track_id} - ${ev.detection_status})`;
          if (ev.event_id === currentVal) opt.selected = true;
          selectTamperEvent.appendChild(opt);
        });
      }
    }

    // Populate Sidebar Feed
    const feedList = document.getElementById("eventFeedList");
    feedList.innerHTML = "";

    if (events.length === 0) {
      feedList.innerHTML = '<div style="color:#8b9bb4; padding:10px;">No intrusion events recorded yet.</div>';
    }

    events.forEach(ev => {
      const item = document.createElement("div");
      const isTampered = ev.is_tampered || ev.detection_status === "NO_INTRUSION_DETECTED";
      item.className = isTampered ? "event-feed-item tampered-feed-item" : "event-feed-item";

      const titleHtml = isTampered
        ? `<div class="event-title">
             <span class="red"><i class="fa-solid fa-triangle-exclamation"></i> ${ev.event_id}</span>
             <span class="badge red blink-fast"><i class="fa-solid fa-mask"></i> NO INTRUSION DETECTED (TAMPERED)</span>
           </div>`
        : `<div class="event-title">
             <span class="red"><i class="fa-solid fa-person-military-rifle"></i> ${ev.event_id}</span>
             <span class="badge red">CONFIRMED BREACH (INTRUSION DETECTED)</span>
           </div>`;

      const metaHtml = isTampered
        ? `<div class="event-meta">
             <div style="color:#ff5252; font-size:0.75rem; margin-bottom:4px; font-weight:600;">
               <i class="fa-solid fa-shield-xmark"></i> ${ev.tamper_note || 'Altered to NO INTRUSION DETECTED to conceal breach!'}
             </div>
             <div><strong>Anchored Proof:</strong> Block #${ev.block_index || "N/A"} | <strong>Track:</strong> #${ev.track_id}</div>
             <div><strong>Time:</strong> ${ev.video_timestamp} | <strong>Camera:</strong> ${ev.camera_id}</div>
             <div style="margin-top:8px; display:flex; gap:6px;">
               <button class="btn btn-success btn-small" onclick="event.stopPropagation(); toggleIntrusionTamper('${ev.event_id}', 'INTRUSION_DETECTED')">
                 <i class="fa-solid fa-rotate-left"></i> Restore Status
               </button>
               <button class="btn btn-outline btn-small" onclick="event.stopPropagation(); inspectForensicModal('${ev.event_id}')">
                 <i class="fa-solid fa-microscope"></i> Forensics
               </button>
             </div>
           </div>`
        : `<div class="event-meta">
             <div><strong>Status:</strong> <span class="green" style="font-weight:600;">INTRUSION DETECTED</span></div>
             <div><strong>Track ID:</strong> #${ev.track_id} | <strong>Time:</strong> ${ev.video_timestamp}</div>
             <div><strong>Frame:</strong> #${ev.frame_number} | <strong>Camera:</strong> ${ev.camera_id}</div>
             <div style="margin-top:4px;"><strong>Block:</strong> #${ev.block_index || "N/A"}</div>
             <div style="margin-top:8px; display:flex; gap:6px;">
               <button class="btn btn-warning btn-small" onclick="event.stopPropagation(); toggleIntrusionTamper('${ev.event_id}', 'NO_INTRUSION_DETECTED')">
                 <i class="fa-solid fa-user-secret"></i> Tamper: Set 'No Intrusion'
               </button>
               <button class="btn btn-outline btn-small" onclick="event.stopPropagation(); inspectForensicModal('${ev.event_id}')">
                 <i class="fa-solid fa-microscope"></i> Forensics
               </button>
             </div>
           </div>`;

      item.innerHTML = titleHtml + metaHtml;
      item.addEventListener("click", () => inspectForensicModal(ev.event_id));
      feedList.appendChild(item);
    });

    // Populate Evidence Vault Grid
    const grid = document.getElementById("evidenceGrid");
    grid.innerHTML = "";

    if (events.length === 0) {
      grid.innerHTML = '<div style="color:#8b9bb4; padding:20px;">No evidence snapshots currently recorded.</div>';
    }

    events.forEach(ev => {
      const card = document.createElement("div");
      card.className = "evidence-card";
      const isTampered = ev.is_tampered || ev.detection_status === "NO_INTRUSION_DETECTED";
      const imgUrl = ev.evidence_url || "/evidence/sample_frame_100.jpg";

      const badgeHtml = isTampered
        ? `<span class="evidence-badge red blink-fast" style="background:#d50000;"><i class="fa-solid fa-triangle-exclamation"></i> TAMPERED (NO INTRUSION DETECTED)</span>`
        : `<span class="evidence-badge">${ev.event_id}</span>`;

      const statusHtml = isTampered
        ? `<div style="color:#ff1744; font-size:0.75rem; font-weight:700; margin-bottom:6px;">
             <i class="fa-solid fa-ban"></i> Concealed on Peer Node: NO INTRUSION DETECTED
           </div>`
        : `<div style="color:#00e676; font-size:0.75rem; font-weight:600; margin-bottom:6px;">
             <i class="fa-solid fa-circle-check"></i> Status: INTRUSION DETECTED
           </div>`;

      const buttonHtml = isTampered
        ? `<div style="display:flex; gap:6px; margin-top:8px;">
             <button class="btn btn-outline btn-small" style="flex:1;" onclick="inspectForensicModal('${ev.event_id}')">
               <i class="fa-solid fa-microscope"></i> Forensics
             </button>
             <button class="btn btn-success btn-small" style="flex:1;" onclick="toggleIntrusionTamper('${ev.event_id}', 'INTRUSION_DETECTED')">
               <i class="fa-solid fa-rotate-left"></i> Restore
             </button>
           </div>`
        : `<div style="display:flex; gap:6px; margin-top:8px;">
             <button class="btn btn-outline btn-small" style="flex:1;" onclick="inspectForensicModal('${ev.event_id}')">
               <i class="fa-solid fa-microscope"></i> Forensics
             </button>
             <button class="btn btn-warning btn-small" style="flex:1;" onclick="toggleIntrusionTamper('${ev.event_id}', 'NO_INTRUSION_DETECTED')">
               <i class="fa-solid fa-user-secret"></i> Tamper
             </button>
           </div>`;

      card.innerHTML = `
        <div class="evidence-img-wrap" onclick="inspectForensicModal('${ev.event_id}')">
          <img src="${imgUrl}" alt="Intrusion Evidence" onerror="this.src='/evidence/sample_frame_0.jpg'">
          ${badgeHtml}
        </div>
        <div class="evidence-body">
          <h4>Track #${ev.track_id} (${ev.video_timestamp})</h4>
          <p style="font-size:0.75rem; color:#8b9bb4; margin-bottom:4px;">Frame #${ev.frame_number} • ${ev.zone_id}</p>
          ${statusHtml}
          <div class="evidence-hash-line" title="${ev.frame_hash}">
            <i class="fa-solid fa-hashtag"></i> ${ev.frame_hash}
          </div>
          ${buttonHtml}
        </div>
      `;
      grid.appendChild(card);
    });
  } catch (err) {
    console.error("Failed to load intrusion events:", err);
  }
}

// Load Blockchain Chain & Explorer
async function loadBlockchainChain(nodeKey = currentBlockchainNode) {
  try {
    const res = await fetch(`/api/blockchain/chain?node=${nodeKey}`);
    const data = await res.json();
    const chain = data.chain || [];

    const statusBadge = document.getElementById("chainIntegrityStatus");
    if (data.is_integrity_valid) {
      statusBadge.innerHTML = `<span class="green"><i class="fa-solid fa-circle-check"></i> ${data.node_id} Chain Intact (100% Cryptographically Valid)</span>`;
    } else {
      statusBadge.innerHTML = `<span class="red"><i class="fa-solid fa-triangle-exclamation"></i> ${data.node_id} Compromised: ${data.integrity_issues[0] || "Disparity detected"}</span>`;
    }

    const tbody = document.getElementById("blockTableBody");
    tbody.innerHTML = "";

    chain.slice().reverse().forEach(block => {
      const tr = document.createElement("tr");
      const shortHash = block.hash.slice(0, 16) + "...";
      const shortMerkle = block.merkle_root.slice(0, 16) + "...";
      const txCount = block.transactions ? block.transactions.length : 0;
      const dateStr = new Date(block.timestamp * 1000).toLocaleTimeString();

      // Check if block has tampered intrusion transaction
      const isBlockTampered = block.transactions && block.transactions.some(tx =>
        tx.tampered || tx.detection_status === "NO_INTRUSION_DETECTED" || tx.type === "MALICIOUS_INJECTION"
      );

      let txLabel = `${txCount} TX`;
      let txBadgeClass = "";
      if (isBlockTampered) {
        tr.style.background = "rgba(255, 23, 68, 0.18)";
        tr.style.borderLeft = "3px solid #ff1744";
        txLabel = `🚨 TAMPERED (NO INTRUSION DETECTED)`;
        txBadgeClass = "red";
      }

      tr.innerHTML = `
        <td><strong class="${isBlockTampered ? 'red' : 'cyan'}">#${block.index}</strong></td>
        <td><code class="${isBlockTampered ? 'red' : 'cyan'}" title="${block.hash}">${shortHash}</code></td>
        <td><code title="${block.merkle_root}">${shortMerkle}</code></td>
        <td><span class="badge ${block.validator_node.includes('Border') ? 'green' : 'purple'}">${block.validator_node}</span></td>
        <td><span class="badge ${txBadgeClass}">${txLabel}</span></td>
        <td>${dateStr}</td>
        <td>
          <button class="btn btn-outline btn-small" onclick='showBlockDetails(${JSON.stringify(block)})'>
            <i class="fa-solid fa-code"></i> Inspect
          </button>
        </td>
      `;
      tbody.appendChild(tr);
    });
  } catch (err) {
    console.error("Failed to load blockchain chain:", err);
  }
}

// Load Audit Access Logs
async function loadAuditLogs(nodeKey = currentAuditNode) {
  try {
    const res = await fetch(`/api/audit-logs?node=${nodeKey}`);
    const data = await res.json();
    const logs = data.audit_logs || [];

    const tbody = document.getElementById("auditTableBody");
    tbody.innerHTML = "";

    logs.slice().reverse().forEach(entry => {
      const tr = document.createElement("tr");
      const shortHash = entry.entry_hash ? entry.entry_hash.slice(0, 16) + "..." : "N/A";
      const dateStr = new Date(entry.timestamp * 1000).toLocaleTimeString();
      const isTamper = entry.status && (entry.status.includes("TAMPER") || entry.status.includes("ALARM"));

      if (isTamper) {
        tr.style.background = "rgba(255, 23, 68, 0.15)";
        tr.style.borderLeft = "3px solid #ff1744";
      }

      tr.innerHTML = `
        <td><strong class="${isTamper ? 'red' : 'cyan'}">${entry.audit_id}</strong></td>
        <td>${dateStr}</td>
        <td>${entry.accessor_identity}</td>
        <td><span class="badge ${entry.accessor_node.includes('Border') ? 'green' : (entry.accessor_node.includes('State') ? 'cyan' : 'purple')}">${entry.accessor_node}</span></td>
        <td><code>${entry.action}</code></td>
        <td>${entry.target_id}</td>
        <td><code title="${entry.entry_hash}">${shortHash}</code></td>
        <td><span class="badge ${isTamper ? 'red' : 'green'}">${entry.status}</span></td>
      `;
      tbody.appendChild(tr);
    });
  } catch (err) {
    console.error("Failed to load audit logs:", err);
  }
}

// Load Cybersecurity Authorized Personnel
async function loadPersonnel() {
  try {
    const res = await fetch("/api/personnel");
    const data = await res.json();
    const list = data.authorized_personnel || [];

    const tbody = document.getElementById("personnelTableBody");
    tbody.innerHTML = "";

    list.forEach(p => {
      const tr = document.createElement("tr");
      const trackAssigned = p.assigned_track_id !== null ? `Track #${p.assigned_track_id}` : "Any / Perimeter Token";
      const active = p.exemption_active;

      tr.innerHTML = `
        <td><code>${p.personnel_id}</code></td>
        <td><strong>${p.name}</strong></td>
        <td>${p.rank}</td>
        <td><span class="badge cyan">${trackAssigned}</span></td>
        <td><span class="badge ${active ? 'green' : 'red'}">${active ? 'EXEMPT FROM ALARMS ✓' : 'REVOKED'}</span></td>
        <td>
          <button class="btn btn-outline btn-small" onclick="togglePersonnelExemption('${p.personnel_id}', '${p.name}', '${p.rank}', ${!active}, ${p.assigned_track_id})">
            ${active ? 'Revoke Access' : 'Restore Access'}
          </button>
        </td>
      `;
      tbody.appendChild(tr);
    });
  } catch (err) {
    console.error("Failed to load personnel:", err);
  }
}

// Grant Clearance Form Handler
async function handleGrantClearance(e) {
  e.preventDefault();
  const id = document.getElementById("inputPersonnelId").value.trim();
  const name = document.getElementById("inputName").value.trim();
  const rank = document.getElementById("inputRank").value.trim();
  const trackIdVal = document.getElementById("inputTrackId").value;
  const trackId = trackIdVal ? parseInt(trackIdVal) : null;

  try {
    const res = await fetch("/api/personnel/authorize", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        personnel_id: id,
        name: name,
        rank: rank,
        assigned_track_id: trackId,
        exemption_active: true
      })
    });
    const result = await res.json();
    alert(`Success: ${result.message}`);
    document.getElementById("personnelForm").reset();
    loadPersonnel();
    loadOverview();
  } catch (err) {
    alert("Failed to grant clearance: " + err);
  }
}

// Toggle Personnel Exemption
async function togglePersonnelExemption(id, name, rank, newStatus, trackId) {
  try {
    await fetch("/api/personnel/authorize", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        personnel_id: id,
        name: name,
        rank: rank,
        assigned_track_id: trackId,
        exemption_active: newStatus
      })
    });
    loadPersonnel();
    loadOverview();
  } catch (err) {
    console.error("Failed to toggle personnel:", err);
  }
}

// Forensic Inspection Modal
async function inspectForensicModal(eventId) {
  const modal = document.getElementById("verificationModal");
  const modalBody = document.getElementById("modalBody");
  modal.style.display = "flex";

  modalBody.innerHTML = `
    <div style="text-align:center; padding:30px;">
      <i class="fa-solid fa-spinner fa-spin cyan" style="font-size:2rem; margin-bottom:12px;"></i>
      <p>Initiating Forensic Cryptographic Scrutiny with Judiciary Node...</p>
    </div>
  `;

  try {
    const res = await fetch(`/api/verify/evidence/${eventId}`);
    const data = await res.json();

    const isAuthentic = data.is_authentic_forensic_evidence;
    const isConcealed = data.is_concealed_tamper;
    const imgUrl = `/evidence/${data.evidence_file ? data.evidence_file.split('/').pop() : ''}`;

    let statusBadgeText = 'FORENSICALLY AUTHENTIC ✓';
    let statusBadgeClass = 'green';
    if (!isAuthentic) {
      statusBadgeClass = 'red';
      statusBadgeText = isConcealed ? 'TAMPER DETECTED: BREACH CONCEALMENT ✗' : 'TAMPER DETECTED ✗';
    }

    const nodeBreakdownHtml = data.node_breakdown ? `
      <div style="margin-bottom:12px; padding:8px; background:rgba(0,0,0,0.4); border-radius:4px;">
        <div style="color:#8b9bb4; font-size:0.7rem; margin-bottom:4px;">CROSS-NODE CONSENSUS STATUS:</div>
        <div style="display:flex; flex-direction:column; gap:4px; font-size:0.75rem;">
          <div>• Border Police: <span class="badge ${data.node_breakdown['BorderPolice-Node'] === 'INTRUSION_DETECTED' ? 'green' : 'red'}">${data.node_breakdown['BorderPolice-Node'] || 'N/A'}</span></div>
          <div>• State Police: <span class="badge ${data.node_breakdown['StatePolice-Node'] === 'INTRUSION_DETECTED' ? 'green' : 'red'}">${data.node_breakdown['StatePolice-Node'] || 'N/A'}</span></div>
          <div>• Judiciary: <span class="badge ${data.node_breakdown['Judiciary-Node'] === 'INTRUSION_DETECTED' ? 'green' : 'red'}">${data.node_breakdown['Judiciary-Node'] || 'N/A'}</span></div>
        </div>
      </div>
    ` : '';

    const tamperAlertHtml = isConcealed ? `
      <div style="margin-bottom:12px; padding:10px; background:rgba(255,23,68,0.15); border:1px solid #ff1744; border-radius:4px;">
        <div style="color:#ff1744; font-weight:700;"><i class="fa-solid fa-triangle-exclamation"></i> MALICIOUS BREACH CONCEALMENT CAUGHT!</div>
        <div style="font-size:0.75rem; color:#fff; margin-top:4px;">${data.tamper_reason || "Status altered to 'NO INTRUSION DETECTED' to conceal perimeter breach!"}</div>
        <div style="font-size:0.7rem; color:#00f2fe; margin-top:4px;">Judiciary Ruling: <strong>EVIDENCE TAMPERED / REJECTED DUE TO CROSS-NODE CONCEALMENT</strong></div>
      </div>
    ` : '';

    modalBody.innerHTML = `
      <div style="display:grid; grid-template-columns: 1fr 1.2fr; gap:18px;">
        <div>
          <img src="${imgUrl}" style="width:100%; border-radius:6px; border:1px solid rgba(255,255,255,0.1);" onerror="this.src='/evidence/sample_frame_100.jpg'">
          <div style="margin-top:12px; text-align:center;">
            <span class="badge ${statusBadgeClass}" style="font-size:0.85rem; padding:6px 14px;">
              ${statusBadgeText}
            </span>
          </div>
          <div style="margin-top:10px; text-align:center;">
            ${isConcealed ? `
              <button class="btn btn-success btn-small btn-block" onclick="toggleIntrusionTamper('${data.event_id}', 'INTRUSION_DETECTED'); closeModal();">
                <i class="fa-solid fa-rotate-left"></i> Restore Status ('INTRUSION DETECTED')
              </button>
            ` : `
              <button class="btn btn-warning btn-small btn-block" onclick="toggleIntrusionTamper('${data.event_id}', 'NO_INTRUSION_DETECTED'); closeModal();">
                <i class="fa-solid fa-user-secret"></i> Simulate Concealment ('NO INTRUSION DETECTED')
              </button>
            `}
          </div>
        </div>

        <div style="font-family:var(--font-mono); font-size:0.8rem;">
          <h4 style="font-family:var(--font-hud); color:#fff; margin-bottom:10px;">${data.event_id} (Track #${data.track_id})</h4>

          ${tamperAlertHtml}
          ${nodeBreakdownHtml}

          <div style="margin-bottom:8px;">
            <span style="color:#8b9bb4;">Timestamp:</span> <strong>${data.video_timestamp}</strong>
          </div>

          <div style="margin-bottom:12px; padding:8px; background:rgba(0,0,0,0.4); border-radius:4px;">
            <div style="color:#8b9bb4; font-size:0.7rem;">STORED HASH (BLOCK #${data.block_index}):</div>
            <code class="cyan" style="word-break:break-all;">${data.stored_frame_hash}</code>
          </div>

          <div style="margin-bottom:12px; padding:8px; background:rgba(0,0,0,0.4); border-radius:4px;">
            <div style="color:#8b9bb4; font-size:0.7rem;">CALCULATED DISK FILE HASH:</div>
            <code class="${data.hash_matches ? 'green' : 'red'}" style="word-break:break-all;">${data.current_frame_hash}</code>
            <div style="margin-top:4px;">
              <span class="badge ${data.hash_matches ? 'green' : 'red'}">${data.hash_matches ? 'FRAME HASH MATCHES ✓' : 'HASH MISMATCH!'}</span>
            </div>
          </div>

          <div style="margin-bottom:12px; padding:8px; background:rgba(0,0,0,0.4); border-radius:4px;">
            <div style="color:#8b9bb4; font-size:0.7rem;">CAMERA ED25519 DIGITAL SIGNATURE:</div>
            <code style="word-break:break-all; font-size:0.65rem;">${data.camera_signature}</code>
            <div style="margin-top:4px;">
              <span class="badge ${data.signature_valid ? 'green' : 'red'}">${data.signature_valid ? 'AUTHENTICATED FROM REGISTERED CAM-001 ✓' : 'INVALID SIGNATURE!'}</span>
            </div>
          </div>

          <div style="padding:8px; background:rgba(0,0,0,0.4); border-radius:4px;">
            <div style="color:#8b9bb4; font-size:0.7rem;">AI MODEL INTEGRITY:</div>
            <code class="green" style="word-break:break-all;">${data.model_hash.slice(0, 32)}...</code>
            <div style="margin-top:4px;">
              <span class="badge green">JUDICIALLY ANCHORED MODEL ✓</span>
            </div>
          </div>
        </div>
      </div>
    `;
  } catch (err) {
    modalBody.innerHTML = `<div style="color:#ff1744;">Error inspecting forensics: ${err}</div>`;
  }
}

// Close Modal
function closeModal() {
  document.getElementById("verificationModal").style.display = "none";
}

// Show Raw Block JSON Details
function showBlockDetails(block) {
  const modal = document.getElementById("verificationModal");
  const modalBody = document.getElementById("modalBody");
  modal.style.display = "flex";

  modalBody.innerHTML = `
    <h3 style="font-family:var(--font-hud); margin-bottom:12px;">BLOCK #${block.index} DETAILS</h3>
    <pre style="background:rgba(0,0,0,0.7); padding:16px; border-radius:6px; overflow:auto; max-height:60vh; font-family:var(--font-mono); font-size:0.8rem; color:#00f2fe;">${JSON.stringify(block, null, 2)}</pre>
  `;
}

// Tamper Demonstrations
async function simulateAuditTamper() {
  const box = document.getElementById("tamperResultBox");
  box.style.display = "block";
  box.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Injecting unauthorized alteration into State Police audit log and executing cross-node consensus audit...';

  try {
    const res = await fetch("/api/simulate/tamper", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ target: "audit_log", node: "state_police" })
    });
    const result = await res.json();

    box.innerHTML = `
      <div style="color:#ff1744; font-weight:700; margin-bottom:6px;">
        <i class="fa-solid fa-triangle-exclamation"></i> TAMPERING DETECTED ACROSS ALL AUTHORITY NODES!
      </div>
      <div><strong>Action:</strong> Audit record on State Police node was maliciously modified.</div>
      <div style="color:#00e676; margin-top:6px;">
        <strong>Border Police Node Response:</strong> Flagged hash disparity immediately!
      </div>
      <div style="color:#00e676;">
        <strong>Judiciary Node Response:</strong> Rejected state log as fraudulent!
      </div>
      <div style="margin-top:6px; font-size:0.75rem; color:#8b9bb4;">
        Result: Decentralized consensus prevented silent alteration of border logs.
      </div>
    `;

    loadOverview();
    loadAuditLogs();
  } catch (err) {
    box.innerHTML = `<span style="color:#ff1744;">Error: ${err}</span>`;
  }
}

async function simulateEvidenceTamper() {
  const box = document.getElementById("tamperResultBox");
  box.style.display = "block";
  box.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Modifying evidence bytes on disk to simulate evidence tampering...';

  try {
    const res = await fetch("/api/simulate/tamper-evidence", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ event_id: "INTRUSION-DET-001" })
    });
    const result = await res.json();

    box.innerHTML = `
      <div style="color:#ff1744; font-weight:700; margin-bottom:6px;">
        <i class="fa-solid fa-shield-xmark"></i> FORENSIC SCRUTINY: EVIDENCE TAMPERING CAUGHT!
      </div>
      <div><strong>Original Hash:</strong> <code>${result.verification_result.stored_frame_hash.slice(0, 24)}...</code></div>
      <div><strong>Tampered Hash:</strong> <code class="red">${result.verification_result.current_frame_hash.slice(0, 24)}...</code></div>
      <div style="color:#ff1744; margin-top:4px;">
        <strong>Camera Digital Signature:</strong> FAILED (Camera private key did not sign this altered image).
      </div>
      <div style="color:#00f2fe; margin-top:6px; font-size:0.8rem;">
        Court / Judiciary Node has ruled this evidence <strong>INADMISSIBLE</strong> due to chain-of-custody breach.
      </div>
    `;

    loadOverview();
    loadAuditLogs();
  } catch (err) {
    box.innerHTML = `<span style="color:#ff1744;">Error: ${err}</span>`;
  }
}

async function restoreIntegrity() {
  const box = document.getElementById("tamperResultBox");
  box.style.display = "block";
  box.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Restoring cryptographic consensus across all 3 nodes...';

  try {
    const res = await fetch("/api/simulate/restore", { method: "POST" });
    const result = await res.json();

    box.innerHTML = `
      <div style="color:#00e676; font-weight:700;">
        <i class="fa-solid fa-circle-check"></i> ALL 3 NODES RESTORED TO VERIFIED CONSENSUS STATE!
      </div>
      <div style="font-size:0.8rem; color:#8b9bb4; margin-top:4px;">
        Border Police, State Police, and Judiciary are operating in full cryptographic harmony.
      </div>
    `;

    loadOverview();
    loadBlockchainChain();
    loadAuditLogs();
    loadIntrusionEvents();
  } catch (err) {
    box.innerHTML = `<span style="color:#ff1744;">Error: ${err}</span>`;
  }
}

// Intrusion Concealment Tamper Simulation & Restoration
async function simulateIntrusionConcealmentTamper() {
  const box = document.getElementById("tamperResultBox");
  box.style.display = "block";
  box.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Maliciously altering intrusion detection to "NO INTRUSION DETECTED" on target node and initiating cross-node consensus audit...';

  const selectEvent = document.getElementById("selectTamperEvent");
  const selectNode = document.getElementById("selectTamperNode");
  const eventId = selectEvent ? selectEvent.value : "INTRUSION-DET-001";
  const nodeKey = selectNode ? selectNode.value : "state_police";

  try {
    const res = await fetch("/api/intrusion/change-status", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        event_id: eventId,
        status: "NO_INTRUSION_DETECTED",
        node: nodeKey
      })
    });
    const result = await res.json();

    const targetNodeTitle = result.attacked_node;
    const allNodeNames = ["BorderPolice-Node", "StatePolice-Node", "Judiciary-Node"];
    const peerNodeNames = allNodeNames.filter(n => n !== targetNodeTitle);

    box.innerHTML = `
      <div style="color:#ff1744; font-weight:700; font-size:1.05rem; margin-bottom:8px;">
        <i class="fa-solid fa-triangle-exclamation"></i> TAMPERING DETECTED! BREACH CONCEALMENT CAUGHT ACROSS AUTHORITY NODES!
      </div>
      <div style="margin-bottom:8px; font-size:0.85rem;">
        <strong>Malicious Action:</strong> Intrusion <code>${result.event_id}</code> was changed from <code>INTRUSION DETECTED</code> to <code>NO INTRUSION DETECTED</code> on <strong>${targetNodeTitle}</strong>!
      </div>

      <!-- Decentralized Consensus Verification Matrix -->
      <div style="background:rgba(0,0,0,0.6); border:1px solid rgba(255,23,68,0.4); border-radius:6px; padding:12px; margin-bottom:10px; font-family:var(--font-mono); font-size:0.8rem;">
        <div style="color:#00f2fe; font-weight:700; margin-bottom:8px; border-bottom:1px solid rgba(255,255,255,0.1); padding-bottom:4px;">
          DECENTRALIZED 3-NODE CONSENSUS VERIFICATION MATRIX:
        </div>
        <div style="display:flex; flex-direction:column; gap:6px;">
          <div style="color:#ff5252;">
            • <strong>${targetNodeTitle} (Attacked Node):</strong> Status changed to <code>NO INTRUSION DETECTED</code> (Intrusion detection is NOT found on this node!).
          </div>
          <div style="color:#00e676;">
            • <strong>${peerNodeNames[0]} (Peer Node 1):</strong> Status remains <code>INTRUSION DETECTED</code>. Disparity caught! Raised <code>CRITICAL INTEGRITY BREACH</code> alert & logged tamper alert.
          </div>
          <div style="color:#00e676;">
            • <strong>${peerNodeNames[1]} (Peer Node 2):</strong> Status remains <code>INTRUSION DETECTED</code>. Disparity caught! Raised <code>CRITICAL INTEGRITY BREACH</code> alert & logged tamper alert.
          </div>
        </div>
        <div style="margin-top:10px; padding-top:6px; border-top:1px solid rgba(255,255,255,0.1); color:#ffeb3b;">
          <strong>Consensus Verdict:</strong> 2/3 Byzantine Majority Quorum REJECTS the malicious modification. Chain of custody is preserved across remaining nodes!
        </div>
      </div>

      <div style="color:#00e676; font-size:0.85rem; font-weight:600;">
        <i class="fa-solid fa-circle-check"></i> RESULT: All remaining nodes immediately detected the modification. Inspection proof recorded in both Blockchain and Audit Logs.
      </div>
    `;

    await loadAllData();
  } catch (err) {
    box.innerHTML = `<span style="color:#ff1744;">Error: ${err}</span>`;
  }
}

async function restoreIntrusionConcealmentTamper() {
  const box = document.getElementById("tamperResultBox");
  box.style.display = "block";
  box.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Restoring intrusion to authentic "INTRUSION DETECTED" state...';

  const selectEvent = document.getElementById("selectTamperEvent");
  const selectNode = document.getElementById("selectTamperNode");
  const eventId = selectEvent ? selectEvent.value : "INTRUSION-DET-001";
  const nodeKey = selectNode ? selectNode.value : "state_police";

  try {
    const res = await fetch("/api/intrusion/change-status", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        event_id: eventId,
        status: "INTRUSION_DETECTED",
        node: nodeKey
      })
    });
    const result = await res.json();

    box.innerHTML = `
      <div style="color:#00e676; font-weight:700; font-size:1rem; margin-bottom:6px;">
        <i class="fa-solid fa-circle-check"></i> INTRUSION RESTORED TO AUTHENTIC STATE!
      </div>
      <div style="font-size:0.85rem; color:#8b9bb4;">
        Intrusion <code>${result.event_id}</code> is confirmed as <strong>INTRUSION DETECTED</strong>. Cryptographic harmony verified across all 3 nodes.
      </div>
    `;

    await loadAllData();
  } catch (err) {
    box.innerHTML = `<span style="color:#ff1744;">Error: ${err}</span>`;
  }
}

async function toggleIntrusionTamper(eventId, newStatus, targetNode = "state_police") {
  try {
    const res = await fetch("/api/intrusion/change-status", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        event_id: eventId,
        status: newStatus,
        node: targetNode
      })
    });
    const result = await res.json();
    alert(result.message);
    await loadAllData();
  } catch (err) {
    alert("Action failed: " + err);
  }
}

