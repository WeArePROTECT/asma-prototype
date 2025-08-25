// src/patients/PatientsList.jsx
import React from "react";
import { Table, Typography, Card } from "antd";
import axios from "axios";

const { Title, Paragraph } = Typography;

export default function PatientsList() {
  const [data, setData] = React.useState([]);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState(null);

  React.useEffect(() => {
    const run = async () => {
      try {
        // use 127.0.0.1 (not localhost) to avoid odd IPv6/host issues
        const res = await axios.get("http://127.0.0.1:8000/patients");
        setData(res.data || []);
      } catch (e) {
        setError(e?.message || String(e));
      } finally {
        setLoading(false);
      }
    };
    run();
  }, []);

  // make columns from keys so we don't have to guess your CSV shape
  const columns = React.useMemo(() => {
    if (!data?.length) return [];
    return Object.keys(data[0]).map((key) => ({
      title: key,
      dataIndex: key,
      key,
    }));
  }, [data]);

  return (
    <Card>
      <Title level={3} style={{ marginBottom: 8 }}>Patients</Title>
      <Paragraph type="secondary" style={{ marginBottom: 16 }}>
        Data fetched from <code>http://127.0.0.1:8000/patients</code>
      </Paragraph>

      {error ? (
        <Paragraph type="danger">Error: {error}</Paragraph>
      ) : (
        <Table
          size="middle"
          rowKey={(r, i) => r.id ?? r.patient_id ?? i}
          columns={columns}
          dataSource={data}
          loading={loading}
          bordered
        />
      )}
    </Card>
  );
}
