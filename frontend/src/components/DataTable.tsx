// src/components/DataTable.tsx (Beautiful Ant Design Table with Entity-Specific Search)
import React, { useEffect, useMemo, useState } from "react";
import { Table, Button, Tag, Space, Input, Card, Typography, Badge } from "antd";
import { SearchOutlined, EyeOutlined, LinkOutlined, DatabaseOutlined } from "@ant-design/icons";
import type { ColumnsType } from "antd/es/table";

const { Title, Text } = Typography;

type Props = {
  rows: any[];
  onOpenLineage?: (row: any) => void;
  onRowDetails?: (row: any) => void;
  onOpenNetworkWithFocus?: (isolateId: string) => void;
  entity: "patients" | "samples" | "bins" | "isolates";
  searchTerm?: string; // Add this prop
};

function toStr(v: any): string {
  if (v == null) return "";
  if (typeof v === "string") return v;
  if (typeof v === "number" || typeof v === "boolean") return String(v);
  try { return JSON.stringify(v); } catch { return ""; }
}

// Helper function to format cell values with enhanced styling
function formatCellValue(value: any) {
  if (value == null) return <span className="text-gray-400 italic">-</span>;
  
  if (typeof value === "boolean") {
    return (
      <Badge 
        status={value ? "success" : "error"} 
        text={value ? "Yes" : "No"}
        className="font-medium"
      />
    );
  }
  
  if (typeof value === "number") {
    return (
      <span className="font-mono font-semibold text-blue-600">
        {value.toLocaleString()}
      </span>
    );
  }
  
  if (Array.isArray(value)) {
    return (
      <Tag color="blue" className="font-medium">
        {value.length} items
      </Tag>
    );
  }
  
  if (typeof value === "object") {
    return <Tag color="orange" className="font-medium">Object</Tag>;
  }
  
  // String values
  const str = String(value);
  if (str.length > 50) {
    return (
      <span title={str} className="text-gray-700">
        {str.substring(0, 47)}...
      </span>
    );
  }
  
  return <span className="text-gray-700 font-medium">{str}</span>;
}

export default function DataTable({
  rows,
  onOpenLineage,
  onRowDetails,
  onOpenNetworkWithFocus,
  entity,
  searchTerm = "", // Add default value
}: Props) {
  // Implement search functionality with entity-specific filtering
  const filteredRows = useMemo(() => {
    // Ensure we only have data for the correct entity
    let entityFilteredRows = rows || [];
    
    // Apply strict entity-specific filtering to prevent cross-contamination
    if (entity === "patients") {
      entityFilteredRows = entityFilteredRows.filter(row => 
        row.patient_id && 
        !row.sample_id && 
        !row.bin_id && 
        !row.isolate_id &&
        row.age !== undefined &&
        row.sex !== undefined &&
        row.condition !== undefined &&
        row.cohort !== undefined
      );
    } else if (entity === "samples") {
      entityFilteredRows = entityFilteredRows.filter(row => 
        row.sample_id && 
        !row.bin_id && 
        !row.isolate_id &&
        row.patient_id !== undefined &&
        (row.sample_type !== undefined || row.type !== undefined) &&
        (row.collection_date !== undefined || row.date !== undefined) &&
        row.project_id !== undefined
      );
    } else if (entity === "bins") {
      entityFilteredRows = entityFilteredRows.filter(row => 
        row.bin_id && 
        !row.isolate_id &&
        row.sample_id !== undefined &&
        row.taxonomy !== undefined &&
        row.abundance !== undefined
      );
    } else if (entity === "isolates") {
      entityFilteredRows = entityFilteredRows.filter(row => 
        row.isolate_id &&
        row.patient_id !== undefined &&
        (row.source_sample_id !== undefined || row.sample_id !== undefined) &&
        row.taxonomy !== undefined
      );
    }
    
    // Apply search filtering if searchTerm is provided
    if (searchTerm && searchTerm.trim()) {
      const searchLower = searchTerm.toLowerCase().trim();
      entityFilteredRows = entityFilteredRows.filter(row => {
        // Entity-specific search fields
        if (entity === "patients") {
          return (
            toStr(row.patient_id).toLowerCase().includes(searchLower) ||
            toStr(row.age).toLowerCase().includes(searchLower) ||
            toStr(row.sex).toLowerCase().includes(searchLower) ||
            toStr(row.condition).toLowerCase().includes(searchLower) ||
            toStr(row.cohort).toLowerCase().includes(searchLower)
          );
        } else if (entity === "samples") {
          return (
            toStr(row.sample_id).toLowerCase().includes(searchLower) ||
            toStr(row.patient_id).toLowerCase().includes(searchLower) ||
            toStr(row.sample_type || row.type).toLowerCase().includes(searchLower) ||
            toStr(row.collection_date || row.date).toLowerCase().includes(searchLower) ||
            toStr(row.project_id).toLowerCase().includes(searchLower)
          );
        } else if (entity === "bins") {
          return (
            toStr(row.bin_id).toLowerCase().includes(searchLower) ||
            toStr(row.sample_id).toLowerCase().includes(searchLower) ||
            toStr(row.taxonomy).toLowerCase().includes(searchLower) ||
            toStr(row.abundance).toLowerCase().includes(searchLower) ||
            toStr(row.pathways).toLowerCase().includes(searchLower)
          );
        } else if (entity === "isolates") {
          return (
            toStr(row.isolate_id).toLowerCase().includes(searchLower) ||
            toStr(row.patient_id).toLowerCase().includes(searchLower) ||
            toStr(row.source_sample_id || row.sample_id).toLowerCase().includes(searchLower) ||
            toStr(row.taxonomy).toLowerCase().includes(searchLower) ||
            toStr(row.amr_flags).toLowerCase().includes(searchLower)
          );
        }
        return false;
      });
    }
    
    return entityFilteredRows;
  }, [rows, entity, searchTerm]);

  const columns = useMemo<ColumnsType<any>>(() => {
    // Entity-specific column definitions with enhanced styling
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
        <span className="font-bold text-gray-800 text-sm">
          {col.title}
        </span>
      ),
      dataIndex: col.key,
      key: col.key,
      render: (value: any) => formatCellValue(value),
      ellipsis: true,
      width: col.width,
    }));

    // Add action column with enhanced styling
    const showLineage = entity === "patients" || entity === "samples";
    const showDetails = entity === "samples" || entity === "bins";
    const showNetwork = entity === "isolates" && !!onOpenNetworkWithFocus;

    if (showLineage || showDetails || showNetwork) {
      baseCols.push({
        title: (
          <span className="font-bold text-gray-800 text-sm">
            Actions
          </span>
        ),
        key: "actions",
        width: 180,
        render: (_, record) => (
          <Space size="small">
            {showLineage && (
              <Button
                type="link"
                size="small"
                icon={<LinkOutlined />}
                className="text-blue-600 hover:text-blue-800 font-medium"
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
                className="text-green-600 hover:text-green-800 font-medium"
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
                className="text-purple-600 hover:text-purple-800 font-medium"
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
    <div className="space-y-4">
      {/* Enhanced Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <DatabaseOutlined className="text-xl text-blue-600" />
          <Title level={4} className="!mb-0 !text-gray-800">
            {entity.charAt(0).toUpperCase() + entity.slice(1)} Data
            {searchTerm && (
              <span className="ml-2 text-sm text-blue-600 font-normal">
                (Searching for "{searchTerm}")
              </span>
            )}
          </Title>
          <Badge count={filteredRows.length} showZero className="bg-blue-500" />
        </div>
      </div>

      {/* Enhanced Table */}
      <Table
        columns={columns}
        dataSource={filteredRows}
        rowKey={(record, index) => {
          // Use a combination of ID and index to ensure uniqueness
          const id = record.id || record.patient_id || record.sample_id || record.bin_id || record.isolate_id;
          return `${id}-${index}`;
        }}
        pagination={{
          pageSize: 10,
          showSizeChanger: true,
          showQuickJumper: true,
          showTotal: (total, range) => 
            `${range[0]}-${range[1]} of ${total} items`,
          pageSizeOptions: ['10', '20', '50', '100'],
          className: "mt-4",
        }}
        scroll={{ x: 'max-content' }}
        size="middle"
        bordered={false}
        onRow={clickable ? (record) => ({
          onClick: () => handleRowClick(record),
          style: { cursor: 'pointer' }
        }) : undefined}
        rowClassName={(record, index) => 
          index % 2 === 0 ? 'bg-blue-50/50 hover:bg-blue-100/50' : 'bg-white hover:bg-gray-50'
        }
        className="shadow-sm rounded-lg overflow-hidden"
        locale={{
          emptyText: (
            <div className="py-12 text-center">
              <DatabaseOutlined className="text-4xl text-gray-300 mb-4" />
              <div className="text-gray-500 text-lg font-medium">
                {searchTerm ? `No results found for "${searchTerm}"` : "No data found"}
              </div>
              <div className="text-gray-400 text-sm">
                {searchTerm ? "Try a different search term" : "No data available for this entity"}
              </div>
            </div>
          )
        }}
      />
    </div>
  );
}
