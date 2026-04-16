import { initDB } from '../db';


/**
 * Service to manage syncing of offline answer attempts to the secure backend.
 * Uses idempotency to guarantee duplicate requests on flaky networks are discarded securely.
 */
export class SyncService {
  /**
   * Main execution loop to be called on network 'online' events or background cycles.
   */
  static async flushPendingAttempts() {
    if (!navigator.onLine) return; // Fast exit if known offline

    const db = await initDB();
    
    // 1. Gather pending attempts
    const tx = db.transaction('offline_attempts', 'readonly');
    const index = tx.store.index('by-status');
    const pending = await index.getAll('pending');
    
    if (pending.length === 0) return;

    // 2. Mark them as syncing locally to prevent duplicate fetch loops before IDB clears
    const markTx = db.transaction('offline_attempts', 'readwrite');
    for (const attempt of pending) {
      attempt.sync_status = 'syncing';
      markTx.store.put(attempt);
    }
    await markTx.done;

    // 3. Dispatch to remote
    try {
      // (Mock URL for the FastAPI backend)
      const res = await fetch('http://localhost:8000/offline/sync/attempts', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          // 'Authorization': `Bearer ${token}` 
        },
        body: JSON.stringify({ attempts: pending })
      });

      if (!res.ok) throw new Error("Sync Rejected by Server");

      // 4. Clean up IDB on success (Backend guarantees idempotency due to UUID)
      const clearTx = db.transaction('offline_attempts', 'readwrite');
      for (const attempt of pending) {
        clearTx.store.delete(attempt.client_attempt_id);
      }
      await clearTx.done;
      
    } catch (e) {
      // 5. Rollback status to pending to retry later
      console.warn("Sync failed, attempts placed back in pending queue.");
      const rollbackTx = db.transaction('offline_attempts', 'readwrite');
      for (const attempt of pending) {
        attempt.sync_status = 'pending';
        rollbackTx.store.put(attempt);
      }
      await rollbackTx.done;
    }
  }

  static registerListeners() {
    window.addEventListener('online', () => {
      console.log('Network connected. Flushing offline queue...');
      this.flushPendingAttempts();
    });
  }
}
