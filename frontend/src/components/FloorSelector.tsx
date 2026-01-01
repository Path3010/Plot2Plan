'use client';

interface FloorSelectorProps {
    floors: number[];
    activeFloor: number;
    onFloorSelect: (floor: number) => void;
}

export default function FloorSelector({ floors, activeFloor, onFloorSelect }: FloorSelectorProps) {
    const floorNames: Record<number, string> = {
        0: 'Ground Floor',
        1: 'First Floor',
        2: 'Second Floor',
        3: 'Third Floor',
    };

    return (
        <div className="flex gap-2 p-1 bg-gray-800 rounded-lg">
            {floors.map((floor) => (
                <button
                    key={floor}
                    onClick={() => onFloorSelect(floor)}
                    className={`px-4 py-2 rounded-md font-medium transition-all ${activeFloor === floor
                            ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg'
                            : 'text-gray-400 hover:text-white hover:bg-gray-700'
                        }`}
                >
                    {floorNames[floor] || `Floor ${floor}`}
                </button>
            ))}
        </div>
    );
}
