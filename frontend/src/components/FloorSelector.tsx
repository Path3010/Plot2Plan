'use client';

interface FloorSelectorProps {
    floors: number[];
    activeFloor: number;
    onFloorSelect: (floor: number) => void;
}

export default function FloorSelector({ floors, activeFloor, onFloorSelect }: FloorSelectorProps) {
    const getFloorName = (floor: number) => {
        if (floor === 0) return 'Ground Floor';
        if (floor === 1) return 'First Floor';
        if (floor === 2) return 'Second Floor';
        if (floor === 3) return 'Third Floor';
        return `Floor ${floor}`;
    };

    return (
        <div className="floor-tabs">
            {floors.map(floor => (
                <button
                    key={floor}
                    onClick={() => onFloorSelect(floor)}
                    className={`floor-tab ${activeFloor === floor ? 'active' : ''}`}
                >
                    {getFloorName(floor)}
                </button>
            ))}
        </div>
    );
}
