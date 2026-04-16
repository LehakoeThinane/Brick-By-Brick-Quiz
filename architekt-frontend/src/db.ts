import { openDB } from 'idb';
import type { DBSchema, IDBPDatabase } from 'idb';

export interface ArchitektDB extends DBSchema {
  categories: {
    key: string; // id
    value: {
      id: string;
      name: string;
      slug: string;
      description?: string;
    };
  };
  questions: {
    key: string;
    value: {
      id: string;
      category_id: string;
      question_text: string;
      options: Record<string, string>;
      difficulty: number;
    };
    indexes: { 'by-category': string };
  };
  mastery_profiles: {
    key: string; // category_id
    value: {
      user_id: string;
      category_id: string;
      state: string; // UNSEEN, ATTEMPTED, STRUGGLING, etc.
    };
  };
  offline_attempts: {
    key: string; // client_attempt_id (UUID)
    value: {
      client_attempt_id: string;
      question_id: string;
      selected_option: string;
      response_time_ms: number;
      answered_at: string;
      sync_status: 'pending' | 'syncing' | 'failed';
    };
    indexes: { 'by-status': string };
  };
}

export const initDB = async (): Promise<IDBPDatabase<ArchitektDB>> => {
  return openDB<ArchitektDB>('architekt-offline', 1, {
    upgrade(db) {
      if (!db.objectStoreNames.contains('categories')) {
        db.createObjectStore('categories', { keyPath: 'id' });
      }
      if (!db.objectStoreNames.contains('questions')) {
        const qStore = db.createObjectStore('questions', { keyPath: 'id' });
        qStore.createIndex('by-category', 'category_id');
      }
      if (!db.objectStoreNames.contains('mastery_profiles')) {
        db.createObjectStore('mastery_profiles', { keyPath: 'category_id' });
      }
      if (!db.objectStoreNames.contains('offline_attempts')) {
        const attemptStore = db.createObjectStore('offline_attempts', { keyPath: 'client_attempt_id' });
        attemptStore.createIndex('by-status', 'sync_status');
      }
    },
  });
};

export const syncOfflineAttempts = async () => {
    // Basic structural concept: fetch pending items and shoot to POST /sync/attempts.
    const db = await initDB();
    const tx = db.transaction('offline_attempts', 'readwrite');
    const store = tx.objectStore('offline_attempts');
    const pending = await store.index('by-status').getAll('pending');
    
    if (pending.length === 0) return;
    
    // Send to backend...
    // In production, map these out via fetch('/offline/sync')
    // After success, delete from IDB or mark as synced.
};
