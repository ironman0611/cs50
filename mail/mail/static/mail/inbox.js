document.addEventListener('DOMContentLoaded', function() {

  // Use buttons to toggle between views
  document.querySelector('#inbox').addEventListener('click', () => load_mailbox('inbox'));
  document.querySelector('#sent').addEventListener('click', () => load_mailbox('sent'));
  document.querySelector('#archived').addEventListener('click', () => load_mailbox('archive'));
  document.querySelector('#compose').addEventListener('click', compose_email);
  document.querySelector('#compose-form').addEventListener('submit', function(event) {
    event.preventDefault();
    send_email();
  });

  // By default, load the inbox
  load_mailbox('inbox');
});

function compose_email() {

  // Show compose view and hide other views
  document.querySelector('#emails-view').classList.add('d-none');
  document.querySelector('#compose-view').classList.remove('d-none');

  // Update active sidebar button
  document.querySelectorAll('.list-group-item').forEach(btn => btn.classList.remove('active'));
  document.querySelector('#compose').classList.add('active');

  // Clear out composition fields
  document.querySelector('#compose-recipients').value = '';
  document.querySelector('#compose-subject').value = '';
  document.querySelector('#compose-body').value = '';
}

async function load_mailbox(mailbox) {
  
  // Show the mailbox and hide other views
  document.querySelector('#emails-view').classList.remove('d-none');
  document.querySelector('#compose-view').classList.add('d-none');

  // Update the mailbox title
  document.querySelector('#mailbox-title').textContent = mailbox.charAt(0).toUpperCase() + mailbox.slice(1);
  
  // Update active sidebar button
  document.querySelectorAll('.list-group-item').forEach(btn => btn.classList.remove('active'));
  document.querySelector(`#${mailbox}`).classList.add('active');
  
  try {
    const response = await fetch(`/emails/${mailbox}`);
    const emails = await response.json();
    
    const emailsList = document.querySelector('#emails-list');
    
    if (emails.length === 0) {
      emailsList.innerHTML = `
        <div class="text-center py-5">
          <i class="bi bi-inbox text-muted" style="font-size: 3rem;"></i>
          <p class="text-muted mt-3">No emails in ${mailbox}</p>
        </div>
      `;
    } else {
      emailsList.innerHTML = emails.map(email => `
        <div class="email-item border-bottom p-3 ${email.read ? 'bg-grey' : 'bg-white'}" onclick="view_email(${email.id})">
          <div class="d-flex justify-content-between align-items-start">
            <div class="flex-grow-1">
              <div class="d-flex align-items-center mb-1">
                <strong class="me-2">${email.sender}</strong>
                <span class="badge bg-${email.read ? 'secondary' : 'primary'}">${email.read ? 'Read' : 'Unread'}</span>
              </div>
              <h6 class="mb-1 ${email.read ? 'text-muted' : 'fw-bold'}">${email.subject}</h6>
              <p class="text-muted mb-0 small">${email.body.substring(0, 100)}${email.body.length > 100 ? '...' : ''}</p>
            </div>
            <div class="text-end">
              <small class="text-muted">${email.timestamp}</small>
            </div>
            <div class="text-end">
              <button class="btn btn-sm btn-primary" onclick="archive_email(${email.id})">Archive</button>
            </div>
          </div>
        </div>
      `).join('');
    }
  } catch (error) {
    console.error('Error loading mailbox:', error);
    document.querySelector('#emails-list').innerHTML = `
      <div class="alert alert-danger m-3" role="alert">
        <i class="bi bi-exclamation-triangle me-2"></i>Error loading emails
      </div>
    `;
  }
}

async function send_email() {
  const recipients = document.querySelector('#compose-recipients').value;
  const subject = document.querySelector('#compose-subject').value;
  const body = document.querySelector('#compose-body').value;
  
  console.log('Sending email:', { recipients, subject, body });
  
  const data = {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ recipients, subject, body }),
  } 
  
  try {
    const response = await fetch('/emails', data);
    console.log('Response status:', response.status);
    
    if (response.ok) {
      load_mailbox('sent');
      document.querySelector('#compose-form').reset();
    } else {
      const errorData = await response.json();
      console.error('Error response:', errorData);
      alert('Error: ' + (errorData.error || 'Failed to send email'));
    }
  } catch (error) {
    console.error('Network error:', error);
    alert('Network error: ' + error.message);
  }
}

async function view_email(email_id) {
  try {
    const response = await fetch(`/emails/${email_id}`);
    const email = await response.json();
    
    // Mark as read
    if (!email.read) {
      await fetch(`/emails/${email_id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ read: true })
      });
    }
    
    // Show email in a modal or dedicated view
    show_email_modal(email);
  } catch (error) {
    console.error('Error viewing email:', error);
    alert('Error loading email');
  }
}

function show_email_modal(email) {
  // Create modal HTML
  const modalHTML = `
    <div class="modal fade" id="emailModal" tabindex="-1">
      <div class="modal-dialog modal-lg">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">${email.subject}</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
          </div>
          <div class="modal-body">
            <div class="mb-3">
              <strong>From:</strong> ${email.sender}
            </div>
            <div class="mb-3">
              <strong>To:</strong> ${email.recipients.join(', ')}
            </div>
            <div class="mb-3">
              <strong>Date:</strong> ${email.timestamp}
            </div>
            <hr>
            <div class="email-body">
              ${email.body.replace(/\n/g, '<br>')}
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
            <button type="button" class="btn btn-primary" onclick="reply_to_email('${email.sender}', '${email.subject}')">
              <i class="bi bi-reply me-1"></i>Reply
            </button>
          </div>
        </div>
      </div>
    </div>
  `;
  
  // Remove existing modal if any
  const existingModal = document.querySelector('#emailModal');
  if (existingModal) {
    existingModal.remove();
  }
  
  // Add modal to body
  document.body.insertAdjacentHTML('beforeend', modalHTML);
  
  // Show modal
  const modal = new bootstrap.Modal(document.querySelector('#emailModal'));
  modal.show();
}

function reply_to_email(sender, subject) {
  // Close modal
  const modal = bootstrap.Modal.getInstance(document.querySelector('#emailModal'));
  modal.hide();
  
  // Switch to compose view
  compose_email();
  
  // Pre-fill fields
  document.querySelector('#compose-recipients').value = sender;
  document.querySelector('#compose-subject').value = subject.startsWith('Re: ') ? subject : `Re: ${subject}`;
  document.querySelector('#compose-body').focus();
}

