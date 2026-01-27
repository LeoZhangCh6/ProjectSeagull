import { 
  LineChart as RechartsLineChart, 
  Line, 
  XAxis, 
  YAxis, 
  Tooltip, 
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';

interface LineChartProps {
  data: { time: string; [key: string]: any }[];
  dataKey: string;
  color?: string;
  name?: string;
  referenceLine?: number;
}

export function LineChart({ 
  data, 
  dataKey, 
  color = '#00E5FF', 
  name,
  referenceLine,
}: LineChartProps) {
  if (data.length === 0) {
    return (
      <div className="w-full h-full flex items-center justify-center text-[var(--text-secondary)]">
        No data
      </div>
    );
  }
  
  // Format time for display
  const formatTime = (time: string) => {
    const date = new Date(time);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };
  
  // Custom tooltip
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded px-3 py-2 text-sm">
          <div className="text-[var(--text-secondary)]">{formatTime(label)}</div>
          <div style={{ color }}>
            {name || dataKey}: {typeof payload[0].value === 'number' 
              ? payload[0].value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })
              : payload[0].value}
          </div>
        </div>
      );
    }
    return null;
  };
  
  return (
    <ResponsiveContainer width="100%" height="100%">
      <RechartsLineChart data={data} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
        <XAxis 
          dataKey="time" 
          tickFormatter={formatTime}
          stroke="#6b7280"
          fontSize={12}
          tickLine={false}
          axisLine={{ stroke: '#2a3548' }}
        />
        <YAxis 
          stroke="#6b7280"
          fontSize={12}
          tickLine={false}
          axisLine={{ stroke: '#2a3548' }}
          tickFormatter={(value) => value.toLocaleString()}
          domain={['auto', 'auto']}
        />
        <Tooltip content={<CustomTooltip />} />
        {referenceLine !== undefined && (
          <ReferenceLine 
            y={referenceLine} 
            stroke="#6b7280" 
            strokeDasharray="3 3" 
          />
        )}
        <Line 
          type="monotone" 
          dataKey={dataKey} 
          stroke={color} 
          strokeWidth={2}
          dot={false}
          activeDot={{ r: 4, fill: color }}
        />
      </RechartsLineChart>
    </ResponsiveContainer>
  );
}
