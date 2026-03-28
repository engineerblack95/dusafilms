// static/movies/js/detail.js

// ==================== CONTINUOUS PLAYBACK ====================
function initializeAutoPlay(relatedMoviesData, currentMovieSlug) {
    var relatedMovies = relatedMoviesData || [];
    var currentMovieIndex = -1;
    var autoPlayEnabled = true;
    var countdownInterval = null;
    var autoPlayTimeout = null;

    for (var i = 0; i < relatedMovies.length; i++) {
        if (relatedMovies[i].slug === currentMovieSlug) {
            currentMovieIndex = i;
            break;
        }
    }

    function highlightUpNext() {
        var nextIndex = currentMovieIndex + 1;
        if (nextIndex < relatedMovies.length) {
            var cards = document.querySelectorAll('.movie-card');
            for (var i = 0; i < cards.length; i++) {
                if (i === nextIndex) {
                    cards[i].classList.add('upnext-active');
                } else {
                    cards[i].classList.remove('upnext-active');
                }
            }
        }
    }

    function showUpNextNotification(title, seconds) {
        seconds = seconds || 5;
        var notification = document.getElementById('upnextNotification');
        if (!notification) return;
        var nextTitleSpan = document.getElementById('nextMovieTitle');
        var countdownSpan = document.getElementById('countdownTimer');
        if (nextTitleSpan) nextTitleSpan.textContent = title;
        notification.classList.add('show');
        var remaining = seconds;
        if (countdownInterval) clearInterval(countdownInterval);
        countdownInterval = setInterval(function() {
            remaining--;
            if (countdownSpan) {
                countdownSpan.textContent = 'Playing in ' + remaining + ' second' + (remaining !== 1 ? 's' : '') + '...';
            }
            if (remaining <= 0) clearInterval(countdownInterval);
        }, 1000);
        setTimeout(function() {
            notification.classList.remove('show');
        }, seconds * 1000);
    }

    window.cancelAutoPlay = function() {
        autoPlayEnabled = false;
        var toggle = document.getElementById('autoplayToggle');
        if (toggle) toggle.checked = false;
        localStorage.setItem('autoplayPreference', 'false');
        if (autoPlayTimeout) clearTimeout(autoPlayTimeout);
    };

    function playNextMovie() {
        var nextIndex = currentMovieIndex + 1;
        if (nextIndex < relatedMovies.length) {
            window.location.href = relatedMovies[nextIndex].url;
        }
    }

    function setupAutoPlay() {
        var video = document.getElementById('mainPlayer');
        var toggle = document.getElementById('autoplayToggle');
        if (!video) return;
        var saved = localStorage.getItem('autoplayPreference');
        if (saved !== null) autoPlayEnabled = saved === 'true';
        if (toggle) toggle.checked = autoPlayEnabled;
        if (toggle) {
            toggle.addEventListener('change', function() {
                autoPlayEnabled = this.checked;
                localStorage.setItem('autoplayPreference', autoPlayEnabled);
            });
        }
        video.addEventListener('ended', function() {
            if (autoPlayEnabled && currentMovieIndex + 1 < relatedMovies.length) {
                showUpNextNotification(relatedMovies[currentMovieIndex + 1].title, 5);
                autoPlayTimeout = setTimeout(function() {
                    if (autoPlayEnabled) playNextMovie();
                }, 5000);
            }
        });
        highlightUpNext();
    }

    setupAutoPlay();
}


// ==================== ANALYTICS TRACKING ====================
function initializeAnalytics(movieSlug) {
    function getCookie(name) {
        var value = null;
        if (document.cookie) {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = cookies[i].trim();
                if (cookie.indexOf(name + '=') === 0) {
                    value = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return value;
    }

    var csrftoken = getCookie('csrftoken');
    if (!csrftoken) {
        csrftoken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
    }

    // Watch Session Tracking
    (function() {
        var video = document.getElementById('mainPlayer');
        if (!video) return;
        var startTime = null, duration = 0, interval = null, active = true, started = false;
        var slug = movieSlug;
        
        function send(action, dur) {
            dur = dur || 0;
            fetch('/analytics/api/track-session/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrftoken },
                body: JSON.stringify({ movie_slug: slug, action: action, duration: dur })
            }).catch(function(e) { console.log('Analytics error:', e); });
        }
        
        function startTracking() {
            if (!active || started) return;
            started = true;
            startTime = Date.now();
            send('start');
            interval = setInterval(function() {
                if (!video.paused && !video.ended) {
                    duration = Math.floor((Date.now() - startTime) / 1000);
                    send('heartbeat', duration);
                }
            }, 10000);
        }
        
        function stopTracking() {
            if (!active || !started) return;
            if (interval) clearInterval(interval);
            send('end', Math.floor((Date.now() - (startTime || Date.now())) / 1000));
            active = false;
        }
        
        video.addEventListener('play', startTracking);
        video.addEventListener('pause', function() { if (interval) clearInterval(interval); });
        video.addEventListener('ended', stopTracking);
        window.addEventListener('beforeunload', function() {
            if (video && !video.ended && !video.paused && started) {
                send('end', Math.floor((Date.now() - (startTime || Date.now())) / 1000));
            }
        });
    })();

    // Download Tracking
    (function() {
        var btn = document.getElementById('downloadButton');
        if (!btn) return;
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            var url = this.href;
            fetch('/analytics/api/track-download/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrftoken },
                body: JSON.stringify({ movie_slug: movieSlug, action: 'start' })
            }).then(function() { window.open(url, '_blank'); }).catch(function() { window.open(url, '_blank'); });
        });
    })();
}


// ==================== COMMENT AND REPLY HANDLING ====================
function initializeComments(isAuthenticated) {
    var currentEditCommentId = null;
    var currentEditReplyId = null;

    function showMessage(msg, type) {
        var div = document.createElement('div');
        div.className = 'comment-message comment-message-' + type;
        div.innerHTML = '<i class="fas ' + (type === 'success' ? 'fa-check-circle' : 'fa-exclamation-circle') + '"></i> ' + msg;
        document.body.appendChild(div);
        setTimeout(function() {
            div.style.opacity = '0';
            setTimeout(function() { div.remove(); }, 300);
        }, 3000);
    }

    function getCsrfToken() {
        var token = document.querySelector('[name=csrfmiddlewaretoken]');
        return token ? token.value : '';
    }

    window.showReplyForm = function(commentId) {
        var form = document.getElementById('replyForm-' + commentId);
        if (form) form.classList.add('show');
    };

    window.hideReplyForm = function(commentId) {
        var form = document.getElementById('replyForm-' + commentId);
        if (form) form.classList.remove('show');
    };

    window.submitReply = async function(commentId) {
        var form = document.getElementById('replyForm-' + commentId);
        if (!form) return;
        var textarea = form.querySelector('.reply-textarea');
        var nameField = form.querySelector('.reply-name-field');
        var hiddenName = form.querySelector('.reply-name-hidden');
        
        var text = textarea ? textarea.value.trim() : '';
        var name = '';
        
        if (isAuthenticated) {
            name = hiddenName ? hiddenName.value : '';
        } else {
            name = nameField ? nameField.value.trim() : '';
            if (!name) {
                showMessage('Please enter your name', 'error');
                if (nameField) nameField.focus();
                return;
            }
        }
        
        if (!text) {
            showMessage('Please enter your reply', 'error');
            if (textarea) textarea.focus();
            return;
        }
        
        var submitBtn = form.querySelector('.btn-submit-reply');
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Posting...';
        }
        
        try {
            var response = await fetch('/api/reply/add/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrfToken() },
                body: JSON.stringify({ comment_id: commentId, text: text, name: name })
            });
            var data = await response.json();
            
            if (data.status === 'success') {
                var repliesContainer = document.getElementById('replies-' + commentId);
                var noRepliesDiv = document.getElementById('noReplies-' + commentId);
                if (noRepliesDiv) noRepliesDiv.remove();
                
                var replyHtml = '<div class="reply-box" id="reply-' + data.reply_id + '" data-reply-id="' + data.reply_id + '">' +
                    '<div class="reply-author"><i class="fas fa-reply-all"></i> ' + escapeHtml(data.user_name) +
                    (data.is_verified ? '<span class="reply-badge">Verified</span>' : '') + '</div>' +
                    '<div class="reply-time">just now</div>' +
                    '<div class="reply-text" id="reply-text-' + data.reply_id + '">' + escapeHtml(data.text) + '</div>';
                if (isAuthenticated && data.is_verified) {
                    replyHtml += '<div class="reply-actions-small">' +
                        '<button class="btn-edit-reply" onclick="showEditReplyModal(' + data.reply_id + ', \'' + escapeHtml(data.text) + '\')">Edit</button>' +
                        '<button class="btn-delete-reply" onclick="deleteReply(' + data.reply_id + ')">Delete</button>' +
                        '</div>';
                }
                replyHtml += '</div>';
                if (repliesContainer) repliesContainer.insertAdjacentHTML('beforeend', replyHtml);
                
                var replyCountSpan = document.querySelector('.reply-count-' + commentId);
                if (replyCountSpan) {
                    var count = parseInt(replyCountSpan.textContent) || 0;
                    replyCountSpan.textContent = count + 1;
                }
                
                if (textarea) textarea.value = '';
                if (!isAuthenticated && nameField) nameField.value = '';
                window.hideReplyForm(commentId);
                showMessage('Reply posted successfully!', 'success');
            } else {
                showMessage(data.message || 'Failed to post reply', 'error');
            }
        } catch (err) {
            console.error(err);
            showMessage('Network error. Please try again.', 'error');
        } finally {
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.innerHTML = '<i class="fas fa-paper-plane"></i> Post Reply';
            }
        }
    };

    window.showEditCommentModal = function(commentId, currentText) {
        currentEditCommentId = commentId;
        var modal = document.getElementById('editCommentModal');
        var textarea = document.getElementById('editCommentText');
        if (modal && textarea) {
            textarea.value = currentText;
            modal.classList.add('show');
        }
    };

    window.closeEditModal = function() {
        var modal = document.getElementById('editCommentModal');
        if (modal) modal.classList.remove('show');
        currentEditCommentId = null;
    };

    window.saveCommentEdit = async function() {
        var newText = document.getElementById('editCommentText');
        if (!newText) return;
        var newTextValue = newText.value.trim();
        if (!newTextValue) {
            showMessage('Comment cannot be empty', 'error');
            return;
        }
        
        try {
            var response = await fetch('/api/comment/edit/' + currentEditCommentId + '/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrfToken() },
                body: JSON.stringify({ text: newTextValue })
            });
            var data = await response.json();
            
            if (data.status === 'success') {
                var commentText = document.getElementById('comment-text-' + currentEditCommentId);
                if (commentText) commentText.textContent = newTextValue;
                showMessage('Comment updated successfully!', 'success');
                window.closeEditModal();
            } else {
                showMessage(data.message || 'Failed to update comment', 'error');
            }
        } catch (err) {
            showMessage('Network error. Please try again.', 'error');
        }
    };

    window.deleteComment = async function(commentId) {
        if (!confirm('Are you sure you want to delete this comment?')) return;
        
        try {
            var response = await fetch('/api/comment/delete/' + commentId + '/', {
                method: 'DELETE',
                headers: { 'X-CSRFToken': getCsrfToken() }
            });
            var data = await response.json();
            
            if (data.status === 'success') {
                var commentBox = document.getElementById('comment-' + commentId);
                if (commentBox) commentBox.remove();
                
                var countSpan = document.getElementById('commentsCount');
                var countInline = document.getElementById('commentsCountInline');
                if (countSpan) {
                    var val = parseInt(countSpan.textContent) || 0;
                    countSpan.textContent = val - 1;
                    if (countInline) countInline.textContent = val - 1;
                }
                showMessage('Comment deleted successfully!', 'success');
            } else {
                showMessage(data.message || 'Failed to delete comment', 'error');
            }
        } catch (err) {
            showMessage('Network error. Please try again.', 'error');
        }
    };

    window.showEditReplyModal = function(replyId, currentText) {
        currentEditReplyId = replyId;
        var modal = document.getElementById('editReplyModal');
        var textarea = document.getElementById('editReplyText');
        if (modal && textarea) {
            textarea.value = currentText;
            modal.classList.add('show');
        }
    };

    window.closeEditReplyModal = function() {
        var modal = document.getElementById('editReplyModal');
        if (modal) modal.classList.remove('show');
        currentEditReplyId = null;
    };

    window.saveReplyEdit = async function() {
        var newText = document.getElementById('editReplyText');
        if (!newText) return;
        var newTextValue = newText.value.trim();
        if (!newTextValue) {
            showMessage('Reply cannot be empty', 'error');
            return;
        }
        
        try {
            var response = await fetch('/api/reply/edit/' + currentEditReplyId + '/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrfToken() },
                body: JSON.stringify({ text: newTextValue })
            });
            var data = await response.json();
            
            if (data.status === 'success') {
                var replyText = document.getElementById('reply-text-' + currentEditReplyId);
                if (replyText) replyText.textContent = newTextValue;
                showMessage('Reply updated successfully!', 'success');
                window.closeEditReplyModal();
            } else {
                showMessage(data.message || 'Failed to update reply', 'error');
            }
        } catch (err) {
            showMessage('Network error. Please try again.', 'error');
        }
    };

    window.deleteReply = async function(replyId) {
        if (!confirm('Are you sure you want to delete this reply?')) return;
        
        try {
            var response = await fetch('/api/reply/delete/' + replyId + '/', {
                method: 'DELETE',
                headers: { 'X-CSRFToken': getCsrfToken() }
            });
            var data = await response.json();
            
            if (data.status === 'success') {
                var replyBox = document.getElementById('reply-' + replyId);
                if (replyBox) replyBox.remove();
                
                var commentId = data.comment_id;
                var replyCountSpan = document.querySelector('.reply-count-' + commentId);
                if (replyCountSpan) {
                    var count = parseInt(replyCountSpan.textContent) || 0;
                    replyCountSpan.textContent = count - 1;
                }
                
                var repliesContainer = document.getElementById('replies-' + commentId);
                if (repliesContainer && repliesContainer.children.length === 0) {
                    repliesContainer.innerHTML = '<div class="no-replies" id="noReplies-' + commentId + '"><i class="far fa-comment-dots"></i> No replies yet. Be the first to reply!</div>';
                }
                
                showMessage('Reply deleted successfully!', 'success');
            } else {
                showMessage(data.message || 'Failed to delete reply', 'error');
            }
        } catch (err) {
            showMessage('Network error. Please try again.', 'error');
        }
    };

    function escapeHtml(unsafe) {
        if (!unsafe) return '';
        return unsafe.replace(/[&<>]/g, function(m) {
            if (m === '&') return '&amp;';
            if (m === '<') return '&lt;';
            if (m === '>') return '&gt;';
            return m;
        });
    }

    // Comment AJAX
    (function() {
        var form = document.getElementById('commentForm');
        if (!form) return;
        var nameInput = document.getElementById('commentName');
        var textarea = document.getElementById('commentText');
        var commentsList = document.getElementById('commentsList');
        var submitBtn = document.getElementById('submitComment');
        var countSpan = document.getElementById('commentsCount');
        var countInline = document.getElementById('commentsCountInline');
        
        form.addEventListener('submit', async function(e) {
            e.preventDefault();
            var text = textarea ? textarea.value.trim() : '';
            var name = '';
            if (isAuthenticated) {
                var hidden = form.querySelector('input[name="name"]');
                name = hidden ? hidden.value : '';
            } else {
                name = nameInput ? nameInput.value.trim() : '';
                if (!name) { showMessage('Please enter your name', 'error'); if (nameInput) nameInput.focus(); return; }
            }
            if (!text) { showMessage('Please enter your comment', 'error'); if (textarea) textarea.focus(); return; }
            
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Posting...';
            }
            
            try {
                var fd = new FormData();
                fd.append('text', text);
                fd.append('name', name);
                var resp = await fetch(form.action, { method: 'POST', headers: { 'X-CSRFToken': getCsrfToken() }, body: fd });
                var data = await resp.json();
                
                if (resp.ok) {
                    var badge = isAuthenticated ? '<span class="comment-author-badge"><i class="fas fa-check-circle"></i> Verified</span>' : '';
                    var newComment = document.createElement('div');
                    newComment.className = 'comment-box';
                    newComment.id = 'comment-' + data.comment_id;
                    newComment.setAttribute('data-comment-id', data.comment_id);
                    newComment.innerHTML = '<div class="comment-author-name"><span><i class="fas fa-user-circle"></i> ' + escapeHtml(name) + '</span>' + badge + '</div>' +
                        '<div class="comment-time">just now</div>' +
                        '<div class="comment-text" id="comment-text-' + data.comment_id + '">' + escapeHtml(text) + '</div>' +
                        '<div class="comment-footer">' +
                        '<button class="btn-reply" onclick="showReplyForm(' + data.comment_id + ')">' +
                        '<i class="fas fa-reply"></i> Reply (<span class="reply-count-' + data.comment_id + '">0</span>)</button>';
                    if (isAuthenticated) {
                        newComment.innerHTML += '<div class="comment-actions">' +
                            '<button class="btn-edit-comment" onclick="showEditCommentModal(' + data.comment_id + ', \'' + escapeHtml(text) + '\')">' +
                            '<i class="fas fa-edit"></i> Edit</button>' +
                            '<button class="btn-delete-comment" onclick="deleteComment(' + data.comment_id + ')">' +
                            '<i class="fas fa-trash-alt"></i> Delete</button></div>';
                    }
                    newComment.innerHTML += '</div><div id="replyForm-' + data.comment_id + '" class="reply-form"></div>' +
                        '<div class="replies-section" id="replies-' + data.comment_id + '"></div>';
                    if (commentsList) commentsList.insertBefore(newComment, commentsList.firstChild);
                    var val = parseInt(countSpan.textContent) || 0;
                    if (countSpan) countSpan.textContent = val + 1;
                    if (countInline) countInline.textContent = val + 1;
                    if (textarea) textarea.value = '';
                    if (!isAuthenticated && nameInput) nameInput.value = '';
                    showMessage('Comment posted!', 'success');
                } else {
                    showMessage('Failed to post comment', 'error');
                }
            } catch(err) {
                showMessage('Network error', 'error');
            } finally {
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = '<i class="fas fa-paper-plane"></i> Post Comment';
                }
            }
        });
    })();
}


// ==================== VIDEO PLAYBACK FIXES ====================
function initializeVideoPlayback() {
    var video = document.getElementById('mainPlayer');
    if (!video) return;
    var isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);
    if (isMobile) {
        video.controls = false;
        video.muted = true;
        var container = document.querySelector('.video-box');
        if (container) {
            var overlay = document.createElement('div');
            overlay.className = 'mobile-overlay';
            overlay.innerHTML = '<div class="mobile-overlay-content"><div style="margin-bottom: 15px;">Tap Play to start video with audio</div><button class="mobile-play-btn"><i class="fas fa-play"></i> Tap to Play</button></div>';
            container.appendChild(overlay);
            var playBtn = overlay.querySelector('.mobile-play-btn');
            if (playBtn) {
                playBtn.onclick = function() {
                    video.controls = true;
                    video.muted = false;
                    video.play().then(function() { overlay.remove(); }).catch(function() { alert('Please tap the video player'); });
                };
            }
            video.onplay = function() { overlay.remove(); };
        }
    } else {
        video.controls = true;
    }
    var preloaded = false;
    video.addEventListener('mouseenter', function() { if (!preloaded) { video.preload = 'auto'; preloaded = true; } });
}


// ==================== INITIALIZE ALL ====================
document.addEventListener('DOMContentLoaded', function() {
    // Initialize autoplay
    if (typeof window.relatedMoviesData !== 'undefined' && window.currentMovieSlug) {
        initializeAutoPlay(window.relatedMoviesData, window.currentMovieSlug);
    }
    
    // Initialize analytics
    if (typeof window.movieSlug !== 'undefined') {
        initializeAnalytics(window.movieSlug);
    }
    
    // Initialize video playback
    initializeVideoPlayback();
    
    // Initialize comments
    var isAuth = window.isAuthenticated === true;
    initializeComments(isAuth);
});