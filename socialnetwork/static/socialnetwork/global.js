function loadPosts() {
    let xhr = new XMLHttpRequest(); // Create a new instance of XMLHttpRequest
    xhr.onreadystatechange = function() { // Event handler called when the request's state changes.
        if (this.readyState === 4) {
            updatePage(xhr); // Call updatePage with the completed request.
        }
    };
    xhr.open("GET", "/socialnetwork/get-global", true); // Initialize a GET request to fetch the list.
    xhr.send(); // Send the request to the server.
}

function updatePage(xhr) {
    if (xhr.status === 200) {
        let response = JSON.parse(xhr.responseText);
        updateList(response.posts, response.comments);
    } else {
        displayError("Error fetching posts: " + xhr.status);
    }
}

function displayError(message) {
    let errorElement = document.getElementById("error");
    if (errorElement) {
        errorElement.innerHTML = message;
    }
}

function updateList(posts, comments) {
    let postsContainer = document.getElementById("my_posts_go_here");

    // Assuming posts are fetched in ascending order, reverse the array to start appending from the most recent
    posts.reverse().forEach(post => {
        let existingPost = document.getElementById(`id_post_div_${post.id}`);
        if (!existingPost) {
            // Create and prepend the new post element
            let postElement = makePostElement(post, currentUserId);
            // Prepend to ensure latest posts are at the top
            if (postsContainer.firstChild) {
                postsContainer.insertBefore(postElement, postsContainer.firstChild);
            } else {
                postsContainer.appendChild(postElement);
            }
        }
    });

    // Update or add comments
    comments.forEach(comment => {
        let existingComment = document.getElementById(`id_comment_div_${comment.id}`);
        if (!existingComment) {
            // If the comment doesn't exist, find its post and append the comment
            let postCommentsContainer = document.getElementById(`my_comments_go_here_for_post_${comment.post_id}`);
            if (postCommentsContainer) {
                let commentElement = makeCommentElement(comment);
                postCommentsContainer.appendChild(commentElement);
            }
        }
    });
}

function makePostElement(post, currentUserId) {
    let profileUrl = post.user.id === currentUserId ? '/socialnetwork/profile' : `/socialnetwork/other_profile/${post.user.id}`;

    // Convert ISO string to Date object and format
    let creationDate = new Date(post.creation_time);
    let formattedDate = creationDate.toLocaleDateString('en-US', { month: 'numeric', day: 'numeric', year: 'numeric' });
    let formattedTime = creationDate.toLocaleTimeString('en-US', { hour: 'numeric', minute: 'numeric', hour12: true });

    let postDiv = document.createElement("div");
    postDiv.id = `id_post_div_${post.id}`;
    postDiv.className = "post_div";
    postDiv.innerHTML = `
        <a href="${profileUrl}" id="id_post_profile_${post.id}">Post by ${post.user.username}</a>
        <span id="id_post_date_time_${post.id}">${formattedDate} ${formattedTime}</span>
        <span id="id_post_text_${post.id}">${post.text}</span>
        <div id="my_comments_go_here_for_post_${post.id}" class="comments-container"></div>
        <div class="comment-box" id="id_comment_form_${post.id}">
            <label>Comment:</label>
            <input type="text" id="id_comment_input_text_${post.id}" name="comment_text"/>
            <button id="id_comment_button_${post.id}" onclick="addComment(${post.id})">Submit</button>
        </div>
    `;
    return postDiv;
}

function makeCommentElement(comment) {
    // Convert ISO string to Date object and format
    let commentDate = new Date(comment.creation_time);
    let formattedCommentDate = commentDate.toLocaleDateString('en-US', { month: 'numeric', day: 'numeric', year: 'numeric' });
    let formattedCommentTime = commentDate.toLocaleTimeString('en-US', { hour: 'numeric', minute: 'numeric', hour12: true });

    // Create the container for the entire comment
    let commentContainerDiv = document.createElement("div");
    commentContainerDiv.className = "comment";
    commentContainerDiv.id = `id_comment_div_${comment.id}`;

    // Set the innerHTML for the container, including all necessary IDs
    commentContainerDiv.innerHTML = `
        <a href="/socialnetwork/other_profile/${comment.creator.id}" id="id_comment_profile_${comment.id}">${comment.creator.username}</a>
        <span id="id_comment_text_${comment.id}">${comment.text}</span>
        <span id="id_comment_date_time_${comment.id}">${formattedCommentDate} ${formattedCommentTime}</span>
    `;

    return commentContainerDiv;
}

function addPost() {
    let postTextElement = document.getElementById("id_post_input_text");
    let postTextValue = postTextElement.value;

    // Clear the input box and any old error messages.
    postTextElement.value = '';
    displayError('');

    let xhr = new XMLHttpRequest();
    xhr.onreadystatechange = function() {
        if (xhr.readyState === XMLHttpRequest.DONE) {
            if (xhr.status === 200) {
                updatePage(xhr);
            } else {
                displayError("Error adding post: " + this.status);
            }
        }
    };
    xhr.open("POST", addPostUrl, true); // tell web browser to do something with the request, in this case, it is a POST request
    xhr.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
    xhr.send(`post_text=${encodeURIComponent(postTextValue)}&csrfmiddlewaretoken=${getCSRFToken()}`);
}

function addComment(postId) {
    let commentTextElement = document.getElementById(`id_comment_input_text_${postId}`);
    let commentTextValue = commentTextElement.value;

    // Clear the input box.
    commentTextElement.value = '';

    let xhr = new XMLHttpRequest();
    xhr.onreadystatechange = function() {
        if (this.readyState === 4) {
            if (this.status === 200) {
                updatePage(xhr)
            } else {
                displayError("Error adding comment: " + this.status);
            }
        }
    };
    xhr.open("POST", addCommentUrl, true);
    xhr.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
    xhr.send(`post_id=${postId}&comment_text=${encodeURIComponent(commentTextValue)}&csrfmiddlewaretoken=${getCSRFToken()}`);
}

function getCSRFToken() {
    let cookies = document.cookie.split(";");
    for (let i = 0; i < cookies.length; i++) {
        let cookie = cookies[i].trim();
        if (cookie.startsWith("csrftoken=")) {
            return cookie.substring("csrftoken=".length);
        }
    }
    return "unknown";
}

