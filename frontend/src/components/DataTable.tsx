// src/components/DataTable.tsx (Beautiful Ant Design Table)
import React, { useEffect, useMemo, useState } from "react";
import { Table, Button, Tag, Space, Input, Card } from "antd";
import { SearchOutlined, EyeOutlined, LinkOutlined } from "@ant-design/icons";
import type { ColumnsType } from "antd/es/table";

type Props = {
  rows: any[];
  onOpenLineage?: (row: any) => void;
  onRowDetails?: (row: any) => void;
  onOpenNetworkWithFocus?: (isolateId: string) => void;
  entity: "patients" | "samples" | "bins" | "isolates";
  query?: string;
  debounceMs?: number;
};

function toStr(v: any): string {
  if (v == null) return "";
  if (typeof v === "string") return v;
  if (typeof v === "number" || typeof v === "boolean") return String(v);
  try { return JSON.stringify(v); } catch { return ""; }
}

// Helper function to format cell values
function formatCellValue(value: any) {
  if (value == null) return "-";
  
  if (typeof value === "boolean") {
    return (
      <Tag color={value ? "green" : "red"}>
        {value ? "Yes" : "No"}
      </Tag>
    );
  }
  
  if (typeof value === "number") {
    return <span className="font-mono">{value.toLocaleString()}</span>;
  }
  
  if (Array.isArray(value)) {
    return (
      <Tag color="blue">
        {value.length} items
      </Tag>
    );
  }
  
  if (typeof value === "object") {
    return <Tag color="orange">Object</Tag>;
  }
  
  // String values
  const str = String(value);
  if (str.length > 50) {
    return (
      <span title={str}>
        {str.substring(0, 47)}...
      </span>
    );
  }
  
  return str;
}

export default function DataTable({
  rows,
  onOpenLineage,
  onRowDetails,
  onOpenNetworkWithFocus,
  entity,
  query,
  debounceMs = 300,
}: Props) {
  const [qLive, setQLive] = useState(query ?? "");
  const [searchText, setSearchText] = useState("");

  useEffect(() => {
    if (query == null) return;
    const t = window.setTimeout(() => setQLive(query), debounceMs);
    return () => window.clearTimeout(t);
  }, [query, debounceMs]);

  // Safe, case-insensitive filter
  const filteredRows = useMemo(() => {
    const needle = (qLive ?? "").trim().toLowerCase();
    if (!needle) return rows || [];
    
    return (rows || []).filter((r) => {
      for (const v of Object.values(r || {})) {
        if (toStr(v).toLowerCase().includes(needle)) return true;
      }
      return false;
    });
  }, [rows, qLive]);

  const columns = useMemo<ColumnsType<any>>(() => {
    // Entity-specific column definitions
    const entityColumns = {
      patients: [
        { key: "patient_id", title: "Patient ID", width: 120 },
        { key: "age", title: "Age", width: 80 },
        { key: "sex", title: "Sex", width: 80 },
        { key: "condition", title: "Condition", width: 120 },
        { key: "cohort", title: "Cohort", width: 100 },
      ],
      samples: [
        { key: "sample_id", title: "Sample ID", width: 120 },
        { key: "patient_id", title: "Patient ID", width: 120 },
        { key: "sample_type", title: "Type", width: 100 },
        { key: "collection_date", title: "Date", width: 120 },
        { key: "project_id", title: "Project", width: 100 },
      ],
      bins: [
        { key: "bin_id", title: "Bin ID", width: 120 },
        { key: "sample_id", title: "Sample ID", width: 120 },
        { key: "taxonomy", title: "Taxonomy", width: 200 },
        { key: "abundance", title: "Abundance", width: 100 },
        { key: "pathways", title: "Pathways", width: 150 },
      ],
      isolates: [
        { key: "isolate_id", title: "Isolate ID", width: 120 },
        { key: "patient_id", title: "Patient ID", width: 120 },
        { key: "source_sample_id", title: "Sample ID", width: 120 },
        { key: "taxonomy", title: "Taxonomy", width: 200 },
        { key: "amr_flags", title: "AMR Flags", width: 150 },
      ],
    };

    const baseCols = (entityColumns[entity] || []).map((col) => ({
      title: (
        <span className="font-semibold text-gray-700">
          {col.title}
        </span>
      ),
      dataIndex: col.key,
      key: col.key,
      render: (value: any) => formatCellValue(value),
      ellipsis: true,
      width: col.width,
    }));

    // Add action column
    const showLineage = entity === "patients" || entity === "samples";
    const showDetails = entity === "samples" || entity === "bins";
    const showNetwork = entity === "isolates" && !!onOpenNetworkWithFocus;

    if (showLineage || showDetails || showNetwork) {
      baseCols.push({
        title: "Actions",
        key: "actions",
        width: 150,
        render: (_, record) => (
          <Space size="small">
            {showLineage && (
              <Button
                type="link"
                size="small"
                icon={<LinkOutlined />}
                onClick={(e) => {
                  e.stopPropagation();
                  onOpenLineage?.(record);
                }}
              >
                Lineage
              </Button>
            )}
            {showDetails && (
              <Button
                type="link"
                size="small"
                icon={<EyeOutlined />}
                onClick={(e) => {
                  e.stopPropagation();
                  onRowDetails?.(record);
                }}
              >
                Details
              </Button>
            )}
            {showNetwork && (
              <Button
                type="link"
                size="small"
                icon={<LinkOutlined />}
                onClick={(e) => {
                  e.stopPropagation();
                  const iso = record.isolate_id || record.id;
                  if (iso) onOpenNetworkWithFocus?.(iso);
                }}
              >
                Network
              </Button>
            )}
          </Space>
        ),
      });
    }

    return baseCols;
  }, [rows, onOpenLineage, onRowDetails, onOpenNetworkWithFocus, entity]);

  const handleRowClick = (record: any) => {
    if (entity === "samples" || entity === "bins") {
      onRowDetails?.(record);
    } else if (entity === "isolates" && onOpenNetworkWithFocus) {
      const iso = record.isolate_id || record.id;
      if (iso) onOpenNetworkWithFocus(iso);
    }
  };

  const clickable = (entity === "samples" || entity === "bins" || (entity === "isolates" && !!onOpenNetworkWithFocus));

  return (
    <Card 
      title={
        <div className="flex items-center justify-between">
          <span className="text-lg font-semibold">
            {entity.charAt(0).toUpperCase() + entity.slice(1)} Data
          </span>
          <Input
            placeholder="Search data..."
            prefix={<SearchOutlined />}
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            style={{ width: 250 }}
            allowClear
          />
        </div>
      }
      className="shadow-lg"
    >
      <Table
        columns={columns}
        dataSource={filteredRows}
        rowKey={(record, index) => record.id || record.patient_id || record.sample_id || record.bin_id || record.isolate_id || index}
        pagination={{
          pageSize: 10,
          showSizeChanger: true,
          showQuickJumper: true,
          showTotal: (total, range) => 
            `${range[0]}-${range[1]} of ${total} items`,
          pageSizeOptions: ['10', '20', '50', '100'],
        }}
        scroll={{ x: 'max-content' }}
        size="middle"
        bordered={false}
        onRow={clickable ? (record) => ({
          onClick: () => handleRowClick(record),
          style: { cursor: 'pointer' }
        }) : undefined}
        rowClassName={(record, index) => 
          index % 2 === 0 ? 'bg-gray-50' : 'bg-white'
        }
        locale={{
          emptyText: (
            <div className="py-8 text-gray-500">
              <SearchOutlined style={{ fontSize: 48, marginBottom: 16 }} />
              <div>No data found</div>
            </div>
          )
        }}
      />
    </Card>
  );
}
