# Stage 1

## REST API Design — Campus Notification Platform

### Core Actions Identified
1. Get all notifications for a student
2. Mark notification as read
3. Send notification (HR/Admin)
4. Get unread notification count

---

### API Endpoints

#### GET /notifications/{student_id}
Fetch all notifications for a student.

**Headers:**

**Response (200):**
```json
{
  "student_id": "123",
  "notifications": [
    {
      "id": "uuid",
      "type": "Placement",
      "message": "Company X hiring",
      "timestamp": "2026-04-22T17:51:18",
      "isRead": false
    }
  ]
}
```

---

#### PATCH /notifications/{notification_id}/read
Mark a notification as read.

**Response (200):**
```json
{
  "id": "uuid",
  "isRead": true
}
```

---

#### POST /notifications/send
Send notification to students.

**Request Body:**
```json
{
  "student_ids": ["123", "456"],
  "type": "Placement",
  "message": "Company X hiring"
}
```

**Response (201):**
```json
{
  "sent": 2,
  "status": "success"
}
```

---

#### GET /notifications/{student_id}/unread-count
Get count of unread notifications.

**Response (200):**
```json
{
  "student_id": "123",
  "unread_count": 5
}
```

---

### Real-Time Notification Mechanism
Use WebSockets for real-time delivery:
- Student connects via WebSocket on login
- Server pushes notification instantly on new event
- Fallback to polling every 30 seconds if WebSocket fails

# Stage 2

## Database Design

### Choice: PostgreSQL (Relational)
**Why:** Structured notification data, need for complex queries, 
ACID compliance for reliable delivery tracking.

### Schema

```sql
CREATE TABLE students (
  id UUID PRIMARY KEY,
  name VARCHAR(255),
  email VARCHAR(255) UNIQUE
);

CREATE TABLE notifications (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  student_id UUID REFERENCES students(id),
  type VARCHAR(50) CHECK (type IN ('Placement', 'Event', 'Result')),
  message TEXT,
  is_read BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT NOW()
);
```

### Queries

```sql
-- Fetch unread notifications for student
SELECT * FROM notifications
WHERE student_id = '1042' AND is_read = FALSE
ORDER BY created_at DESC;

-- Mark as read
UPDATE notifications SET is_read = TRUE WHERE id = 'uuid';
```

### Problems at scale (50K students, 5M notifications)
- Full table scans slow without indexes
- Single DB becomes bottleneck

### Solutions
- Add composite index on (student_id, is_read, created_at)
- Partition table by student_id range
- Archive old notifications to cold storage

# Stage 3

## Query Analysis

### Original Query:
```sql
SELECT * FROM notifications
WHERE studentID = 1042 AND isRead = false
ORDER BY createdAt DESC;
```

### Is it accurate? Yes — logic is correct.

### Why is it slow?
- No index on studentID or isRead columns
- Full table scan on 5M rows
- SELECT * fetches all columns unnecessarily

### Fix:
```sql
-- Add composite index
CREATE INDEX idx_notifications_student_unread 
ON notifications(studentID, isRead, createdAt DESC);

-- Optimized query — select only needed columns
SELECT id, type, message, createdAt 
FROM notifications
WHERE studentID = 1042 AND isRead = false
ORDER BY createdAt DESC
LIMIT 50;
```

### Adding indexes on every column — bad idea
- Write operations slow down significantly
- Index maintenance overhead
- Only index columns used in WHERE/ORDER BY clauses

# Stage 4

## Performance Optimization

### Problem: DB overwhelmed on every page load

### Strategies:

**1. Redis Caching (Recommended)**
- Cache unread notifications per student
- TTL: 60 seconds
- Invalidate cache on new notification or read event
- Tradeoff: Slight staleness vs massive DB relief

**2. Pagination**
- Never fetch all notifications at once
- Fetch top 20, load more on scroll
- Reduces query size significantly

**3. Read Replicas**
- Route GET queries to read replica
- Write operations go to primary DB
- Tradeoff: Slight replication lag

**Best approach: Caching + Pagination together**

# Stage 5

## Redesigning notify_all for Reliability

### Problems with current implementation:
- Sequential processing — 50K students takes too long
- If send_email fails at student 200, remaining 49800 get nothing
- No retry mechanism
- DB save and email not atomic

### Revised Pseudocode:

# Push to message queue for async email
enqueue_emails(saved_ids, message)

# Push real-time notification
push_to_app(batch, message)