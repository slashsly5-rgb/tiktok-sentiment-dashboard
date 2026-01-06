/**
 * TikTok Political Sentiment Dashboard
 * Project S - Main Application JavaScript
 */

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
  console.log('Project S Dashboard Initialized');

  // Initialize components
  initializeSentimentChart();
  initializeMapInteractions();
  initializeChatInterface();
  initializeDataRefresh();
});

/**
 * Initialize Sentiment Donut Chart
 */
function initializeSentimentChart() {
  const ctx = document.getElementById('sentimentChart');

  if (!ctx) {
    console.warn('Sentiment chart canvas not found');
    return;
  }

  const sentimentChart = new Chart(ctx.getContext('2d'), {
    type: 'doughnut',
    data: {
      labels: ['Positive Comments', 'Negative Comments', 'Neutral Comments'],
      datasets: [{
        data: [45, 33, 22],
        backgroundColor: [
          '#2ECC71', // Positive - Green
          '#E74C3C', // Negative - Red
          '#95A5A6'  // Neutral - Gray
        ],
        borderWidth: 0,
        hoverOffset: 10,
        hoverBorderColor: '#FFFFFF',
        hoverBorderWidth: 3
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      plugins: {
        legend: {
          display: false
        },
        tooltip: {
          backgroundColor: '#2C2C2C',
          titleColor: '#FFFFFF',
          bodyColor: '#FFFFFF',
          borderColor: '#F39C12',
          borderWidth: 2,
          padding: 12,
          displayColors: true,
          callbacks: {
            label: function(context) {
              const label = context.label || '';
              const value = context.parsed || 0;
              return `${label}: ${value}%`;
            }
          }
        }
      },
      cutout: '70%',
      animation: {
        animateRotate: true,
        animateScale: true,
        duration: 1000,
        easing: 'easeInOutQuart'
      }
    }
  });

  console.log('Sentiment chart initialized');
}

/**
 * Initialize Map Interactions
 */
function initializeMapInteractions() {
  const mapRegions = document.querySelectorAll('.map-region');

  mapRegions.forEach(region => {
    // Add click event
    region.addEventListener('click', function() {
      const regionName = this.getAttribute('data-region');
      showRegionDetails(regionName);
    });

    // Enhanced hover effect
    region.addEventListener('mouseenter', function() {
      this.style.filter = 'brightness(1.2) drop-shadow(0 0 8px rgba(0,0,0,0.3))';
    });

    region.addEventListener('mouseleave', function() {
      this.style.filter = '';
    });
  });

  console.log(`Map interactions initialized for ${mapRegions.length} regions`);
}

/**
 * Show Region Details
 */
function showRegionDetails(regionName) {
  // This would typically fetch data from API
  console.log(`Showing details for: ${regionName}`);

  // Example: Show modal or update sidebar with region details
  alert(`Region: ${regionName}\n\nClick OK to view detailed sentiment analysis for this region.`);

  // In production, you would:
  // - Fetch region-specific data from your API
  // - Display in a modal or side panel
  // - Show charts and detailed metrics
}

/**
 * Initialize Chat Interface
 */
function initializeChatInterface() {
  const chatInput = document.querySelector('.chat-input');
  const chatAddBtn = document.querySelector('.chat-add-btn');
  const chatVoiceBtn = document.querySelector('.chat-voice-btn');
  const suggestionChips = document.querySelectorAll('.suggestion-chip');

  // Handle chat input submission
  if (chatInput) {
    chatInput.addEventListener('keypress', function(e) {
      if (e.key === 'Enter') {
        handleChatSubmit(this.value);
        this.value = '';
      }
    });
  }

  // Handle suggestion chip clicks
  suggestionChips.forEach(chip => {
    chip.addEventListener('click', function() {
      const question = this.textContent.trim();
      handleChatSubmit(question);
    });
  });

  // Voice button (placeholder)
  if (chatVoiceBtn) {
    chatVoiceBtn.addEventListener('click', function() {
      console.log('Voice input requested');
      alert('Voice input feature coming soon!');
      // In production: Integrate Web Speech API
    });
  }

  console.log('Chat interface initialized');
}

/**
 * Handle Chat Submission
 */
function handleChatSubmit(message) {
  if (!message || message.trim() === '') {
    return;
  }

  console.log('User message:', message);

  // Display loading state
  showChatLoading();

  // Simulate API call (replace with actual API endpoint)
  setTimeout(() => {
    const response = generateMockResponse(message);
    displayChatResponse(response);
  }, 1500);
}

/**
 * Show Chat Loading State
 */
function showChatLoading() {
  const chatWelcome = document.querySelector('.chat-welcome h3');
  if (chatWelcome) {
    chatWelcome.textContent = 'BUMI is thinking...';
    chatWelcome.classList.add('loading');
  }
}

/**
 * Display Chat Response
 */
function displayChatResponse(response) {
  const chatWelcome = document.querySelector('.chat-welcome h3');
  if (chatWelcome) {
    chatWelcome.textContent = response;
    chatWelcome.classList.remove('loading');
  }

  // In production, you would:
  // - Create a proper chat message UI
  // - Show response in a chat bubble
  // - Maintain conversation history
}

/**
 * Generate Mock Response (for demo purposes)
 */
function generateMockResponse(message) {
  const responses = {
    'cost of living': 'Cost of living is trending up due to inflation and increased urban development. Key concerns include housing prices (+12%) and fuel costs (+8%) in the past quarter.',
    'miri': 'Sentiment in Miri shows neutral to slightly negative trends. Main issues include infrastructure concerns and employment opportunities. Recent engagement: 234 videos analyzed.',
    'default': 'Based on recent TikTok sentiment analysis, I can help you with that. Could you provide more specific details about what you\'d like to know?'
  };

  const lowerMessage = message.toLowerCase();

  for (const [key, response] of Object.entries(responses)) {
    if (lowerMessage.includes(key)) {
      return response;
    }
  }

  return responses.default;
}

/**
 * Initialize Auto Data Refresh
 */
function initializeDataRefresh() {
  // Auto-refresh data every 5 minutes
  const REFRESH_INTERVAL = 5 * 60 * 1000; // 5 minutes

  setInterval(() => {
    console.log('Auto-refreshing dashboard data...');
    refreshDashboardData();
  }, REFRESH_INTERVAL);

  console.log(`Auto-refresh initialized (every ${REFRESH_INTERVAL / 1000}s)`);
}

/**
 * Refresh Dashboard Data
 */
function refreshDashboardData() {
  // Fetch latest data from API
  fetch('/api/dashboard/summary')
    .then(response => response.json())
    .then(data => {
      updateDashboardWithNewData(data);
    })
    .catch(error => {
      console.error('Error refreshing data:', error);
    });
}

/**
 * Update Dashboard with New Data
 */
function updateDashboardWithNewData(data) {
  // Update sentiment badge
  updateSentimentBadge(data.overall_sentiment);

  // Update stats
  updateStats(data.stats);

  // Update charts
  updateCharts(data.charts);

  // Update timestamp
  updateLastRefreshTime();

  console.log('Dashboard updated with latest data');
}

/**
 * Update Sentiment Badge
 */
function updateSentimentBadge(sentiment) {
  const badge = document.querySelector('.sentiment-badge');
  if (badge) {
    // Remove all sentiment classes
    badge.classList.remove('positive', 'negative', 'neutral');

    // Add appropriate class
    if (sentiment >= 7) {
      badge.classList.add('positive');
      badge.textContent = 'Very Positive';
    } else if (sentiment >= 5) {
      badge.classList.add('positive');
      badge.textContent = 'Moderately Positive';
    } else if (sentiment >= 3) {
      badge.classList.add('neutral');
      badge.textContent = 'Neutral';
    } else {
      badge.classList.add('negative');
      badge.textContent = 'Negative';
    }
  }
}

/**
 * Update Stats Cards
 */
function updateStats(stats) {
  if (!stats) return;

  // Update stat values
  const statValues = document.querySelectorAll('.stat-value');
  if (statValues.length >= 4) {
    statValues[0].textContent = stats.total_videos || '0';
    statValues[1].textContent = `${stats.positive_sentiment || '0'}%`;
    statValues[2].textContent = stats.trending_topics || '0';
    statValues[3].textContent = stats.critical_issues || '0';
  }
}

/**
 * Update Charts
 */
function updateCharts(chartsData) {
  if (!chartsData) return;

  // Update sentiment chart
  const chartCanvas = document.getElementById('sentimentChart');
  if (chartCanvas && Chart.getChart(chartCanvas)) {
    const chart = Chart.getChart(chartCanvas);
    chart.data.datasets[0].data = [
      chartsData.positive || 45,
      chartsData.negative || 33,
      chartsData.neutral || 22
    ];
    chart.update();
  }
}

/**
 * Update Last Refresh Time
 */
function updateLastRefreshTime() {
  const timestamp = document.querySelector('.map-timestamp');
  if (timestamp) {
    const now = new Date();
    const formatted = now.toLocaleDateString('en-GB') + ' at ' +
                     now.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' });
    timestamp.textContent = `Last updated at ${formatted}`;
  }
}

/**
 * Utility: Debounce Function
 */
function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

/**
 * Utility: Format Number
 */
function formatNumber(num) {
  if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + 'M';
  } else if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'K';
  }
  return num.toString();
}

/**
 * Utility: Animate Counter
 */
function animateCounter(element, start, end, duration) {
  const startTime = Date.now();
  const range = end - start;

  function update() {
    const now = Date.now();
    const elapsed = now - startTime;
    const progress = Math.min(elapsed / duration, 1);

    const current = Math.floor(start + range * progress);
    element.textContent = formatNumber(current);

    if (progress < 1) {
      requestAnimationFrame(update);
    }
  }

  update();
}

/**
 * Export for external use
 */
window.DashboardApp = {
  refreshData: refreshDashboardData,
  updateSentimentBadge,
  updateStats,
  handleChatSubmit,
  formatNumber,
  animateCounter
};

console.log('Dashboard App loaded successfully');
