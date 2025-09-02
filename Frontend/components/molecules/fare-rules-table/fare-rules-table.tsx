import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"

// Define types for clarity
interface FareRuleDetail {
  od_pair: string;
  min_amount: number | null;
  max_amount: number | null;
  currency: string | null;
  interpretation: string;
}

interface Passenger {
  type: string;
  count: number;
  baggage: {
    carryOn: string;
    checked: string;
  };
  fare_rules: Record<string, Record<string, FareRuleDetail>>;
}

interface FareRulesTableProps {
  passenger: Passenger;
  allOds: string[]; // Pass all unique O&D pairs to ensure consistent column rendering
}

export function FareRulesTable({ passenger, allOds }: FareRulesTableProps) {
  if (!passenger || !passenger.fare_rules) {
    return <p className="text-sm text-muted-foreground p-4">No fare rules available for this passenger.</p>;
  }

  const penaltyTypes = Object.keys(passenger.fare_rules);

  return (
    <div className="rounded-lg border mb-6">
      <div className="p-3 sm:p-4 md:p-6 bg-muted/50 rounded-t-lg">
        <h3 className="text-base sm:text-lg font-semibold">{passenger.count} x {passenger.type}</h3>
        <p className="text-xs sm:text-sm text-muted-foreground mt-1">
          <span className="font-medium">Carry-on:</span> {passenger.baggage.carryOn || 'As per airline policy'} | <span className="font-medium">Checked:</span> {passenger.baggage.checked || 'As per airline policy'}
        </p>
      </div>

      {/* Mobile-first responsive design */}
      <div className="block md:hidden">
        {/* Mobile Card Layout */}
        <div className="p-3 space-y-4">
          {penaltyTypes.length === 0 ? (
            <div className="text-center text-muted-foreground py-8">
              No specific penalty rules were provided for this fare.
            </div>
          ) : (
            penaltyTypes.map(penaltyType => {
              const timings = Object.keys(passenger.fare_rules[penaltyType]);
              return (
                <div key={penaltyType} className="border rounded-lg p-3">
                  <h4 className="font-medium text-sm mb-3">{penaltyType}</h4>
                  {timings.map(timing => {
                    const rule = passenger.fare_rules[penaltyType][timing];
                    const feeText = (min: number | null, max: number | null, currency: string | null) => {
                      if (min === null && max === null) return "N/A";
                      if (min === max) return `${max} ${currency}`;
                      return `${min} - ${max} ${currency}`;
                    };

                    return (
                      <div key={timing} className="mb-3 last:mb-0">
                        <div className="text-xs font-medium text-muted-foreground mb-1">{timing}</div>
                        <div className="text-sm">
                          <span className="font-medium">{rule?.od_pair || 'N/A'}:</span>{' '}
                          {rule ? feeText(rule.min_amount, rule.max_amount, rule.currency) : 'N/A'}
                        </div>
                        {rule?.interpretation && (
                          <div className="text-xs text-muted-foreground mt-1 italic">
                            {rule.interpretation}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              );
            })
          )}
        </div>
      </div>

      {/* Desktop Table Layout */}
      <div className="hidden md:block overflow-x-auto">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-[120px] lg:w-[150px] font-semibold text-xs lg:text-sm">Fare Rule</TableHead>
              <TableHead className="font-semibold text-xs lg:text-sm">Timing</TableHead>
              {allOds.map(od => (
                <TableHead key={od} colSpan={2} className="text-center border-l font-semibold text-xs lg:text-sm">
                  {od}
                </TableHead>
              ))}
              <TableHead className="font-semibold text-xs lg:text-sm border-l">Interpretation</TableHead>
            </TableRow>
            <TableRow>
              <TableHead></TableHead>
              <TableHead></TableHead>
              {allOds.map(od => (
                <>
                  <TableHead key={`${od}-min`} className="text-center border-l text-xs text-muted-foreground">MIN</TableHead>
                  <TableHead key={`${od}-max`} className="text-center text-xs text-muted-foreground">MAX</TableHead>
                </>
              ))}
              <TableHead className="text-center border-l text-xs text-muted-foreground">Meaning</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {penaltyTypes.length === 0 ? (
              <TableRow>
                <TableCell colSpan={3 + allOds.length * 2} className="text-center text-muted-foreground h-24 text-xs lg:text-sm">
                  No specific penalty rules were provided for this fare.
                </TableCell>
              </TableRow>
            ) : (
              penaltyTypes.map(penaltyType => {
                const timings = Object.keys(passenger.fare_rules[penaltyType]);
                return timings.map((timing, timingIndex) => (
                  <TableRow key={`${penaltyType}-${timing}`}>
                    {timingIndex === 0 && (
                      <TableCell rowSpan={timings.length} className="font-medium align-top text-xs lg:text-sm">
                        {penaltyType}
                      </TableCell>
                    )}
                    <TableCell className="text-xs lg:text-sm">{timing}</TableCell>
                    {allOds.map(odHeader => {
                      const rule = passenger.fare_rules[penaltyType]?.[timing];
                      // Check if the rule is for the current O&D column
                      if (rule && rule.od_pair === odHeader) {
                        const feeText = (min: number | null, max: number | null, currency: string | null) => {
                          if (min === null && max === null) return "N/A";
                          if (min === max) return `${max} ${currency}`;
                          return `${min} - ${max} ${currency}`;
                        };

                        return (
                          <>
                            <TableCell key={`${odHeader}-min-val`} className="text-center border-l text-xs lg:text-sm">
                              {feeText(rule.min_amount, rule.max_amount, rule.currency)}
                            </TableCell>
                            <TableCell key={`${odHeader}-max-val`} className="text-center text-xs lg:text-sm">
                              {feeText(rule.min_amount, rule.max_amount, rule.currency)}
                            </TableCell>
                          </>
                        );
                      }
                      // Render empty cells if no rule applies for this O&D and timing
                      return (
                        <>
                          <TableCell key={`${odHeader}-min-val`} className="text-center border-l text-xs lg:text-sm">-</TableCell>
                          <TableCell key={`${odHeader}-max-val`} className="text-center text-xs lg:text-sm">-</TableCell>
                        </>
                      );
                    })}
                    <TableCell className="text-xs lg:text-sm border-l">
                      {(() => {
                        // Find the rule for this timing to get the interpretation
                        const rule = passenger.fare_rules[penaltyType]?.[timing];
                        return rule?.interpretation || '-';
                      })()}
                    </TableCell>
                  </TableRow>
                ));
              })
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}