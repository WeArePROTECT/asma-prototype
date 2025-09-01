import React from "react";
import { Card, Descriptions, Tag, Progress, Statistic, Row, Col, Divider, Typography } from "antd";
import { 
  UserOutlined, 
  ExperimentOutlined, 
  DatabaseOutlined, 
  BugOutlined,
  ArrowRightOutlined,
  CalendarOutlined,
  NumberOutlined
} from "@ant-design/icons";

const { Title, Text } = Typography;

type LineageData = {
  patient?: any;
  sample?: any;
  samples?: any[];
  bins?: any[];
  isolates?: any[];
};

type Props = {
  lineage: LineageData;
  entity: "patients" | "samples";
  onClose: () => void;
};

export default function LineageView({ lineage, entity, onClose }: Props) {
  const isPatient = entity === "patients";
  const isSample = entity === "samples";
  
  // Calculate statistics
  const sampleCount = lineage.samples?.length || 0;
  const binCount = lineage.bins?.length || 0;
  const isolateCount = lineage.isolates?.length || 0;
  
  // Calculate average abundance across bins
  const avgAbundance = lineage.bins?.length 
    ? (lineage.bins.reduce((sum, bin) => sum + (bin.abundance || 0), 0) / lineage.bins.length).toFixed(3)
    : "0.000";
  
  // Get unique taxonomic groups
  const uniqueTaxa = new Set(
    lineage.bins?.map(bin => bin.taxonomy?.split(';')[0]).filter(Boolean) || []
  );
  
  // Get unique isolate species
  const uniqueSpecies = new Set(
    lineage.isolates?.map(iso => iso.taxonomy?.split(' ').slice(0, 2).join(' ')).filter(Boolean) || []
  );

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={onClose}>
      <div 
        className="bg-white rounded-lg shadow-2xl max-w-6xl w-full max-h-[90vh] overflow-auto p-6" 
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <Title level={2} className="mb-1">
              <DatabaseOutlined className="mr-2" />
              Data Lineage
            </Title>
            <Text type="secondary">
              {isPatient ? `Patient ${lineage.patient?.patient_id}` : `Sample ${lineage.sample?.sample_id}`}
            </Text>
          </div>
          <button 
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 text-xl"
          >
            ×
          </button>
        </div>

        {/* Overview Statistics */}
        <Card className="mb-6">
          <Row gutter={16}>
            <Col span={6}>
              <Statistic
                title="Samples"
                value={sampleCount}
                prefix={<ExperimentOutlined />}
                valueStyle={{ color: '#1890ff' }}
              />
            </Col>
            <Col span={6}>
              <Statistic
                title="Metagenomic Bins"
                value={binCount}
                prefix={<DatabaseOutlined />}
                valueStyle={{ color: '#52c41a' }}
              />
            </Col>
            <Col span={6}>
              <Statistic
                title="Isolates"
                value={isolateCount}
                prefix={<BugOutlined />}
                valueStyle={{ color: '#fa8c16' }}
              />
            </Col>
            <Col span={6}>
              <Statistic
                title="Avg Abundance"
                value={avgAbundance}
                precision={3}
                prefix={<NumberOutlined />}
                valueStyle={{ color: '#722ed1' }}
              />
            </Col>
          </Row>
        </Card>

        {/* Data Flow Visualization */}
        <div className="mb-6">
          <Title level={4} className="mb-4">Data Flow</Title>
          <div className="flex items-center justify-center space-x-8">
            {/* Patient */}
            {isPatient && (
              <>
                <Card className="w-48 text-center">
                  <UserOutlined className="text-3xl text-blue-500 mb-2" />
                  <div className="font-semibold">Patient</div>
                  <div className="text-sm text-gray-600">{lineage.patient?.patient_id}</div>
                  <div className="text-xs text-gray-500 mt-1">
                    {lineage.patient?.condition} • {lineage.patient?.age} years
                  </div>
                </Card>
                <ArrowRightOutlined className="text-2xl text-gray-400" />
              </>
            )}

            {/* Sample */}
            <Card className="w-48 text-center">
              <ExperimentOutlined className="text-3xl text-green-500 mb-2" />
              <div className="font-semibold">Sample</div>
              <div className="text-sm text-gray-600">
                {isPatient ? `${sampleCount} samples` : lineage.sample?.sample_id}
              </div>
              {isSample && (
                <div className="text-xs text-gray-500 mt-1">
                  {lineage.sample?.type} • {lineage.sample?.date}
                </div>
              )}
            </Card>
            <ArrowRightOutlined className="text-2xl text-gray-400" />

            {/* Bins */}
            <Card className="w-48 text-center">
              <DatabaseOutlined className="text-3xl text-purple-500 mb-2" />
              <div className="font-semibold">Metagenomic Bins</div>
              <div className="text-sm text-gray-600">{binCount} bins</div>
              <div className="text-xs text-gray-500 mt-1">
                {uniqueTaxa.size} unique taxa
              </div>
            </Card>
            <ArrowRightOutlined className="text-2xl text-gray-400" />

            {/* Isolates */}
            <Card className="w-48 text-center">
              <BugOutlined className="text-3xl text-orange-500 mb-2" />
              <div className="font-semibold">Isolates</div>
              <div className="text-sm text-gray-600">{isolateCount} isolates</div>
              <div className="text-xs text-gray-500 mt-1">
                {uniqueSpecies.size} unique species
              </div>
            </Card>
          </div>
        </div>

        <Divider />

        {/* Detailed Information */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Patient/Sample Details */}
          <Card title={isPatient ? "Patient Information" : "Sample Information"}>
            <Descriptions column={1} size="small">
              {isPatient && lineage.patient && (
                <>
                  <Descriptions.Item label="Patient ID">{lineage.patient.patient_id}</Descriptions.Item>
                  <Descriptions.Item label="Age">{lineage.patient.age} years</Descriptions.Item>
                  <Descriptions.Item label="Condition">
                    <Tag color="blue">{lineage.patient.condition}</Tag>
                  </Descriptions.Item>
                  <Descriptions.Item label="Cohort">
                    <Tag color="green">{lineage.patient.cohort}</Tag>
                  </Descriptions.Item>
                </>
              )}
              {isSample && lineage.sample && (
                <>
                  <Descriptions.Item label="Sample ID">{lineage.sample.sample_id}</Descriptions.Item>
                  <Descriptions.Item label="Patient ID">{lineage.sample.patient_id}</Descriptions.Item>
                  <Descriptions.Item label="Type">
                    <Tag color="blue">{lineage.sample.type}</Tag>
                  </Descriptions.Item>
                  <Descriptions.Item label="Date">
                    <CalendarOutlined className="mr-1" />
                    {lineage.sample.date}
                  </Descriptions.Item>
                  <Descriptions.Item label="Project">{lineage.sample.project_id}</Descriptions.Item>
                </>
              )}
            </Descriptions>
          </Card>

          {/* Sample List (for patients) */}
          {isPatient && lineage.samples && (
            <Card title="Samples Collected">
              <div className="space-y-2">
                {lineage.samples.map((sample) => (
                  <div key={sample.sample_id} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                    <div>
                      <div className="font-medium">{sample.sample_id}</div>
                      <div className="text-sm text-gray-600">{sample.type} • {sample.date}</div>
                    </div>
                    <Tag color="green">{sample.project_id}</Tag>
                  </div>
                ))}
              </div>
            </Card>
          )}
        </div>

        {/* Bins Analysis */}
        {lineage.bins && lineage.bins.length > 0 && (
          <Card title="Metagenomic Bins Analysis" className="mt-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Abundance Distribution */}
              <div>
                <h4 className="font-semibold mb-3">Abundance Distribution</h4>
                <div className="space-y-2">
                  {lineage.bins
                    .sort((a, b) => (b.abundance || 0) - (a.abundance || 0))
                    .slice(0, 5)
                    .map((bin) => (
                      <div key={bin.bin_id} className="flex items-center justify-between">
                        <span className="text-sm truncate flex-1 mr-2">{bin.bin_id}</span>
                        <Progress 
                          percent={Math.round((bin.abundance || 0) * 100)} 
                          size="small" 
                          showInfo={false}
                          strokeColor="#52c41a"
                        />
                        <span className="text-xs text-gray-500 ml-2 w-12 text-right">
                          {(bin.abundance || 0).toFixed(3)}
                        </span>
                      </div>
                    ))}
                </div>
              </div>

              {/* Taxonomic Distribution */}
              <div>
                <h4 className="font-semibold mb-3">Top Taxonomic Groups</h4>
                <div className="space-y-2">
                  {Array.from(uniqueTaxa)
                    .slice(0, 5)
                    .map((taxon) => {
                      const count = lineage.bins?.filter(bin => 
                        bin.taxonomy?.startsWith(taxon)
                      ).length || 0;
                      return (
                        <div key={taxon} className="flex items-center justify-between">
                          <span className="text-sm truncate flex-1 mr-2">{taxon}</span>
                          <Tag color="purple">{count} bins</Tag>
                        </div>
                      );
                    })}
                </div>
              </div>
            </div>
          </Card>
        )}

        {/* Isolates Summary */}
        {lineage.isolates && lineage.isolates.length > 0 && (
          <Card title="Isolates Summary" className="mt-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Species Distribution */}
              <div>
                <h4 className="font-semibold mb-3">Species Distribution</h4>
                <div className="space-y-2">
                  {Array.from(uniqueSpecies)
                    .slice(0, 5)
                    .map((species) => {
                      const count = lineage.isolates?.filter(iso => 
                        iso.taxonomy?.startsWith(species)
                      ).length || 0;
                      return (
                        <div key={species} className="flex items-center justify-between">
                          <span className="text-sm truncate flex-1 mr-2">{species}</span>
                          <Tag color="orange">{count} isolates</Tag>
                        </div>
                      );
                    })}
                </div>
              </div>

              {/* AMR Summary */}
              <div>
                <h4 className="font-semibold mb-3">AMR Resistance Summary</h4>
                <div className="space-y-2">
                  {lineage.isolates
                    .filter(iso => iso.amr_flags && iso.amr_flags.length > 0)
                    .slice(0, 5)
                    .map((iso) => (
                      <div key={iso.isolate_id} className="flex items-center justify-between">
                        <span className="text-sm truncate flex-1 mr-2">{iso.isolate_id}</span>
                        <div className="flex gap-1">
                          {iso.amr_flags?.slice(0, 2).map((flag, idx) => (
                            <Tag key={idx} color="red" size="small">{flag}</Tag>
                          ))}
                          {iso.amr_flags && iso.amr_flags.length > 2 && (
                            <Tag color="red" size="small">+{iso.amr_flags.length - 2}</Tag>
                          )}
                        </div>
                      </div>
                    ))}
                </div>
              </div>
            </div>
          </Card>
        )}

        {/* Footer */}
        <div className="mt-6 text-center text-gray-500 text-sm">
          <Text>
            This lineage shows the complete data flow from {isPatient ? 'patient' : 'sample'} through 
            metagenomic analysis to isolate characterization
          </Text>
        </div>
      </div>
    </div>
  );
}
