import { useCallback, useEffect, useRef, useState } from 'react';
import type { WSMessage } from '../types';

interface UseWebSocketOptions {
  onMessage?: (message: WSMessage) => void;
  onOpen?: () => void;
  onClose?: () => void;
  onError?: (error: Event) => void;
}

export function useWebSocket(sessionId: string | undefined, options: UseWebSocketOptions = {}) {
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<number>();
  
  // Use refs for callbacks to avoid stale closures
  const onMessageRef = useRef(options.onMessage);
  const onOpenRef = useRef(options.onOpen);
  const onCloseRef = useRef(options.onClose);
  const onErrorRef = useRef(options.onError);
  
  // Keep refs updated
  useEffect(() => {
    onMessageRef.current = options.onMessage;
    onOpenRef.current = options.onOpen;
    onCloseRef.current = options.onClose;
    onErrorRef.current = options.onError;
  }, [options.onMessage, options.onOpen, options.onClose, options.onError]);
  
  const send = useCallback((data: object) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data));
      return true;
    }
    return false;
  }, []);
  
  const startSimulation = useCallback((testNames?: string[]) => {
    return send({ action: 'start', test_names: testNames });
  }, [send]);
  
  const stopSimulation = useCallback(() => {
    return send({ action: 'stop' });
  }, [send]);
  
  const connect = useCallback(() => {
    if (!sessionId) return;
    
    // Close existing connection
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/simulation/${sessionId}`;
    
    console.log('[WebSocket] Connecting to:', wsUrl);
    
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;
    
    ws.onopen = () => {
      console.log('[WebSocket] Connected');
      setIsConnected(true);
      onOpenRef.current?.();
    };
    
    ws.onclose = (event) => {
      console.log('[WebSocket] Closed:', event.code, event.reason);
      setIsConnected(false);
      wsRef.current = null;
      onCloseRef.current?.();
    };
    
    ws.onerror = (error) => {
      console.error('[WebSocket] Error:', error);
      onErrorRef.current?.(error);
    };
    
    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data) as WSMessage;
        console.log('[WebSocket] Message:', message.type);
        onMessageRef.current?.(message);
      } catch (e) {
        console.error('[WebSocket] Failed to parse message:', e);
      }
    };
  }, [sessionId]);
  
  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    setIsConnected(false);
  }, []);
  
  // Connect when sessionId changes
  useEffect(() => {
    if (sessionId) {
      connect();
    }
    return () => disconnect();
  }, [sessionId, connect, disconnect]);
  
  return {
    isConnected,
    connect,
    disconnect,
    send,
    startSimulation,
    stopSimulation,
  };
}
