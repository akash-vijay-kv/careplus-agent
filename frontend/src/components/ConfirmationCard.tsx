interface ConfirmationCardProps {
  title: string;
  details: Record<string, string>;
  onConfirm: () => void;
  onCancel: () => void;
}

function ConfirmationCard({
  title,
  details,
  onConfirm,
  onCancel,
}: ConfirmationCardProps) {
  return (
    <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 my-2 max-w-sm">
      <h4 className="font-semibold text-gray-800 mb-2">{title}</h4>
      <div className="space-y-1 mb-3">
        {Object.entries(details).map(([key, value]) => (
          <div key={key} className="flex justify-between text-sm">
            <span className="text-gray-500">{key}:</span>
            <span className="text-gray-700 font-medium">{value}</span>
          </div>
        ))}
      </div>
      <div className="flex gap-2">
        <button
          onClick={onConfirm}
          className="flex-1 bg-careplus text-white text-sm py-1.5 rounded-lg hover:bg-careplus-dark transition-colors"
        >
          Confirm
        </button>
        <button
          onClick={onCancel}
          className="flex-1 bg-white text-gray-600 text-sm py-1.5 rounded-lg border border-gray-200 hover:bg-gray-50 transition-colors"
        >
          Cancel
        </button>
      </div>
    </div>
  );
}

export default ConfirmationCard;
