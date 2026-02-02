import { useEffect, useRef } from 'react';
import { createChart, IChartApi, ISeriesApi, CandlestickData, Time } from 'lightweight-charts';
import type { BarData } from '../../types';

interface CandlestickChartProps {
  data: BarData[];
  trades?: TradeEvent[];
}

export function CandlestickChart({ data }: CandlestickChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null);
  
  // Initialize chart
  useEffect(() => {
    if (!containerRef.current) return;
    
    const chart = createChart(containerRef.current, {
      layout: {
        background: { color: '#0b0f19' },
        textColor: '#9ca3af',
      },
      grid: {
        vertLines: { color: '#2a3548' },
        horzLines: { color: '#2a3548' },
      },
      crosshair: {
        mode: 1,
      },
      rightPriceScale: {
        borderColor: '#2a3548',
      },
      timeScale: {
        borderColor: '#2a3548',
        timeVisible: true,
        secondsVisible: false,
      },
    });
    
    const series = chart.addCandlestickSeries({
      upColor: '#00D97E',
      downColor: '#FF6B6B',
      borderUpColor: '#00D97E',
      borderDownColor: '#FF6B6B',
      wickUpColor: '#00D97E',
      wickDownColor: '#FF6B6B',
    });
    
    chartRef.current = chart;
    seriesRef.current = series;
    
    // Handle resize
    const handleResize = () => {
      if (containerRef.current && chartRef.current) {
        chartRef.current.applyOptions({
          width: containerRef.current.clientWidth,
          height: containerRef.current.clientHeight,
        });
      }
    };
    
    window.addEventListener('resize', handleResize);
    handleResize();
    
    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
    };
  }, []);
  
  // Update data
  useEffect(() => {
    if (!seriesRef.current || data.length === 0) return;
    
    const chartData: CandlestickData<Time>[] = data.map(bar => ({
      time: (bar.timestamp / 1000) as Time, // Convert ms to seconds
      open: bar.open,
      high: bar.high,
      low: bar.low,
      close: bar.close,
    }));
    
    seriesRef.current.setData(chartData);
    
    // Omit trade markers - too cluttered; trade info shown in Recent Trades table below
    seriesRef.current.setMarkers([]);
    
    // Fit content
    if (chartRef.current) {
      chartRef.current.timeScale().fitContent();
    }
  }, [data]);
  
  return <div ref={containerRef} className="w-full h-full" />;
}
